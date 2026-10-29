**The published stride-one gated GRU uses a fixed four-sample input history plus a 32-number recurrent memory. It was trained through progressively longer prediction sequences of 1, 8, 16, and 32 steps. Those are different dimensions of the model.**

I checked the conversation records, the frozen cloud input package, the actual worker and model code inside that package, the completed training history, and the selected checkpoint. The package hashes match its recorded preparation proof. The report, checkpoint, and saved predictions match their output manifest. **I made no changes and ran no training or model inference.**

I am describing the model labelled **“Stride-one gated · split 0”** in the current gallery. The older **“4-state gated GRU”** uses byte-identical model code, but different training data and runs. They are not the same trained weights.

**1. What the conversation actually establishes**

I found these explicit statements in our saved conversation, with dates in Pacific time:

| When | What I said |
|---|---|
| October 23, 10:46 p.m. | “I’m fixing the design at a **four-snapshot history**”—this initially described the MLP. |
| October 24, 12:49 a.m., when preparing the GRU comparison | “Both models will start fresh and progress through **1-, 8-, 16- and 32-step training chains**.” |
| October 24, 12:53 a.m. | “Its training memory will be built from the observed history before each window; full-rollout evaluation will use only its own predictions after the initial state.” |
| October 25, 9:37 p.m. | My hyperparameter table separately listed **“Explicit state history: Last 4 frames”** and **“Training rollout length: Progresses through 1, 8, 16, 32 steps.”** |
| October 26, 10:23 p.m. | You answered **“Keep curriculum, stride one at every stage”** to the question explicitly naming the 1/8/16/32 curriculum. |

**I did not find a statement specifying 1, 2, 4, 8, and 16 previous-history items in the available saved records.** That is a limit of what I found, not grounds to dismiss your recollection.

My response earlier today—“I gave you the wrong schedule earlier”—was unjustified because I had not located the statement being disputed. I then answered about forecast length when you were asking about history. That made the confusion worse.

Here are the quantities that must remain separate:

| Quantity | Actual implementation |
|---|---|
| Physical variables in each state | **4** |
| Explicit recent samples supplied at each step | **4 samples**, fixed |
| Numbers in that explicit history | **4 × 4 = 16 numbers** |
| Recurrent hidden memory | **32 numbers** |
| Consecutive predictions used for training | **1 → 8 → 16 → 32 steps** |
| Full-sequence prediction | **90 steps**, approximately 180 seconds |

There is **no implemented curriculum that expands the explicit input history from 1 to 2 to 4 to 8 to 16 samples** in this run.

**2. What one physical state contains**

Each simulation sample contains:

| Variable | Meaning |
|---|---|
| Water, kg | Estimated remaining water in the vegetation |
| Dry fuel, kg | Estimated remaining unreacted vegetation |
| Fuel-gas release, kg/s | Gas leaving the vegetation; **not combustion heat release** |
| Surface-heating index, K | Remaining-particle-mass-weighted temperature above ambient, divided by initial wet mass; **not stored energy or simply temperature** |

These are derived FDS quantities, not four independent direct instrument readings. Water and dry fuel are reconstructed using cumulative release quantities; the dry-fuel reconstruction uses the assumed **0.75 gas yield**. Heating includes the remaining particle material.

The model predicts these aggregate quantities. It does not predict a spatial flame, plume, neighbouring-tree ignition, or heat transport between trees.

**3. Exactly what enters the network**

To predict sample \(n+1\), the explicit history is:

\[
[S_{n-3},S_{n-2},S_{n-1},S_n].
\]

Each \(S\) has four variables. These four samples are **flattened into 16 numbers**.

They are concatenated with these nine inputs:

| External input | Divided by |
|---|---:|
| Crown-height parameter | 10 |
| Fuel-loading multiplier | 1 |
| Wind speed along +X | 5 |
| Cosine of ignition angle | 1 |
| Sine of ignition angle | 1 |
| Initial water mass | 10 |
| Initial dry-fuel mass | 10 |
| Fraction of the next interval for which the ignitor is on | 1 |
| Actual interval duration in seconds | 2 |

That gives **25 inputs at each recurrent step**.

Initial water and dry-fuel masses remain available throughout prediction. Wind direction is fixed by this dataset. Ignition is represented by its angle and known on/off schedule, not a general three-dimensional ignition location or measured incoming heat.

The four history samples are **not processed as four separate GRU steps**. Their flattened vector is one input to one GRU step. The recurrent memory arrives separately.

The saved samples are approximately two seconds apart, not exactly two seconds apart. Across this dataset, adjacent intervals range approximately **1.80–2.20 seconds**. The actual interval is supplied to the model. [Frozen input schema](/Users/wdavies/pi/wildfire3d/experiments/36_tree_density/data/pair-sequence/rotation0/schema.json)

**4. The numerical representation**

The network operates on transformed values, not directly on kilograms and kelvins:

\[
z_f=\frac{\operatorname{asinh}(S_f/a_f)-\mu_f}{\sigma_f},
\qquad
a=[1,\;1,\;0.01,\;100].
\]

The mean and standard deviation are fitted **only using training configurations**, averaging replicas and times within configurations and giving configurations equal weight. The standard deviation has a minimum of 0.05.

Physical predictions are recovered using:

\[
\widehat S_f=a_f\,\sinh(\widehat z_f\sigma_f+\mu_f).
\]

Consequently, a squared error in the training loss is an error in this transformed space. It is not directly a squared error in kg or K, and a gate scaling a mass update scales the **transformed update**, not a kilogram decrement.

**5. The GRU and the additional output gates**

The model consists of:

- One unidirectional GRU layer: **25 inputs, 32 hidden-memory values**.
- A linear head: **32 → 4**, producing proposed state changes.
- A second linear head: **32 → 3**, producing gate logits.
- **5,895 trainable parameters**.
- No dropout, attention, extra recurrent layers, or physical conservation solver.

The GRU already has internal gates that control its memory. **The three added output gates are a separate mechanism.** Calling both simply “gates” without distinguishing them was confusing.

At each step:

1. The GRU reads the 25 inputs and previous hidden memory.
2. It produces updated hidden memory.
3. The four-output head proposes changes in normalized state.
4. Those changes are multiplied by **actual interval / 2 seconds**.
5. The three gate logits pass through sigmoid, producing values between zero and one.

Writing the proposed normalized change as \(\delta\):

| Output | Actual operation |
|---|---|
| Water | \(z'_{\rm water}=z_{\rm water}+g_{\rm water}\delta_{\rm water}\) |
| Dry fuel | \(z'_{\rm fuel}=z_{\rm fuel}+g_{\rm fuel}\delta_{\rm fuel}\) |
| Gas | Form the proposed next gas value, then multiply that value by \(g_{\rm gas}\) in the inverse-asinh space, and transform it back |
| Heating | \(z'_{\rm heat}=z_{\rm heat}+\delta_{\rm heat}\); **no added output gate** |

The gas operation is equivalent to multiplying the proposed physical release rate by its gate. Thus a small gas gate suppresses release toward zero rather than freezing the previous release rate.

These are **soft gates**, not hard switches. They can reopen. There is no permanent “extinguished” latch.

They also do **not** guarantee physical validity:

- Water and fuel can increase.
- Any output can become negative.
- Gas release is not constrained to equal fuel consumption.
- Heating is not tied to an energy-conservation equation.
- There is no output clipping that conceals these failures.

The four-change head starts with zero weights and biases. The gate head starts with zero weights and biases of 4, so its initial gates are approximately **0.982**. A subtle consequence: the untrained gated model initially leaves water/fuel/heating unchanged, but attenuates a nonzero gas value slightly. It is not exactly a no-change predictor for all four outputs. [Exact gated model](/Users/wdavies/pi/wildfire3d/experiments/36_tree_density/data/pair-sequence/rotation0/gated_model.py:7)

**6. How the extra gates are taught**

The gates receive explicit training labels derived from simulation changes. They are not learned solely through the next-state prediction error.

For each target sample, labels use the preceding **up to five saved intervals**, approximately ten seconds:

- Water activity: positive water loss divided by initial water and elapsed time.
- Dry-fuel activity: positive dry-fuel loss divided by initial dry fuel and elapsed time.
- Gas activity: integrated positive gas release, divided by 0.75, initial dry fuel, and elapsed time.

For each of the three rates:

| Rate, fraction of initial mass per second | Gate supervision |
|---|---|
| Below \(10^{-5}\) | Target **0** |
| At least \(10^{-4}\) | Target **1** |
| Between those thresholds | No direct gate-label loss |

The state-prediction loss still applies in the intermediate region.

The gate-label loss is binary cross-entropy, averaged over the supervised gates at that target, multiplied by **0.1**.

**This approximately ten-second trailing calculation is used to construct gate labels. It is not a smoothing kernel applied to the plotted simulation curves.** Negative release and negative mass-loss increments are clipped to zero for these label calculations; that does not impose the same clipping on model outputs. [Gate-label construction](/Users/wdavies/pi/wildfire3d/experiments/36_tree_density/model_evaluation/prepare_pair.py:8)

**7. Exactly how a training example works**

Suppose a window starts at sample \(n=20\), with training length \(H=16\).

**First, prepare its starting state:**

- Explicit history comes from actual simulation samples **17, 18, 19, 20**.
- Hidden memory is reconstructed by passing the actual earlier input sequence through the GRU, starting with zero memory.
- This reconstruction uses the model’s current weights.
- It runs under **`no_grad`**: no gradient propagates through that earlier prefix.

**Then predict the training sequence:**

- Predict sample 21.
- Compare it with actual simulation sample 21.
- Drop the oldest history item and append predicted sample 21.
- Predict sample 22 using that updated history and carried memory.
- Continue through predicted sample 36.
- Compare **every predicted step**, not just sample 36, with its simulation target.

After the window begins, later true states are used as **targets**, not substituted into the prediction history.

The errors are backpropagated through all 16 predicted steps, through both the recurrent memory and the predicted-state feedback. Then the optimizer updates the weights.

A new sampled window starts with its own reconstructed actual-history memory. Memory is **not carried between unrelated windows or simulations**.

This means:

> The memory may contain information from the whole earlier simulation prefix, but the gradient reaches backward only through the current prediction window—at most 32 steps in this run.

It was **not trained by backpropagating through complete 90-step autonomous histories**, even though those full histories were used for validation. [History, prefix and rollout functions](/Users/wdavies/pi/wildfire3d/experiments/36_tree_density/data/pair-sequence/rotation0/worker.py:37)

**8. The actual curriculum and overlapping windows**

Each history contains 91 samples and 90 transitions.

| Epochs | Self-fed training length | Approximate duration | Full windows per history |
|---|---:|---:|---:|
| 1–20 | 1 step | 2 seconds | 90 |
| 21–40 | 8 steps | 16 seconds | 83 |
| 41–60 | 16 steps | 32 seconds | 75 |
| 61 onward | 32 steps | 64 seconds | 59 |

The explicit input history remains **four samples throughout all four stages**.

Stride one means using every valid start. At length 16:

```text
Start 0: predict samples 1–16
Start 1: predict samples 2–17
Start 2: predict samples 3–18
...
Start 74: predict samples 75–90
```

There are no shortened final windows in this stride-one run. Every epoch shuffles all windows for its current stage and processes them in batches of up to **256 windows**.

Overlapping windows expose some transitions repeatedly, especially away from sequence boundaries. They are additional training contexts, not independent simulations. [Frozen curriculum](/Users/wdavies/pi/wildfire3d/experiments/36_tree_density/data/pair-sequence/rotation0/coverage-plan.json)

**9. The loss and optimizer**

At each predicted step, the state loss is:

\[
L_{\rm state}
=\frac{
e_{\rm water}^2+e_{\rm fuel}^2+e_{\rm gas}^2+e_{\rm heat}^2
}{3}.
\]

The divisor really is **3 despite there being four outputs**. This retained the original three-state loss scale when heating was added.

For the gated model:

\[
L_{\rm step}=L_{\rm state}+0.1\,L_{\rm gate}.
\]

This combined loss is multiplied by a transition weight.

Training defines “active” using a separate, permissive rule:

- Next-sample gas release greater than \(10^{-6}\) kg/s, **or**
- Absolute water or fuel change greater than \(10^{-5}\) kg per step.

Within each training history, active and quiet transitions are assigned equal total base weight when both categories exist. The weights also divide by the number of replicas of that configuration.

**That training activity definition is different from the gate-label thresholds and the newer scorecard activity definition.** They must not be conflated.

The weighted losses are summed across the batch and prediction steps, then divided by the number of predicted steps—not by the sum of weights. Because overlapping windows repeat transitions unequally near the boundaries, the original base weighting does not guarantee an exact 50/50 contribution to the final overlapping-window objective.

Actual optimizer settings:

| Setting | Value |
|---|---:|
| Optimizer | AdamW |
| Learning rate | 0.0003, constant |
| Weight decay | 0.0001 |
| Adam betas | 0.9, 0.999 |
| Adam epsilon | \(10^{-8}\) |
| Gradient-norm clipping | 1.0 |
| Initialization seed | 3516 |
| Maximum epochs | 400 |
| Earliest patience-based stopping | Epoch 100 |

No learning-rate decay or dropout is present. I verified these optimizer settings in the saved checkpoint, rather than relying only on the configuration description. [Training loop](/Users/wdavies/pi/wildfire3d/experiments/36_tree_density/data/pair-sequence/rotation0/worker.py:119)

**10. What data it actually trained on and how the checkpoint was chosen**

The latest published gated model uses one fixed grouped split:

| Partition | Histories | Distinct configurations |
|---|---:|---:|
| Training | 1,662 | 1,632 |
| Validation | 210 | 204 |
| Test | 208 | 204 |

Replicas remain together. This is **one 8-train/1-validation/1-test rotation**, not a ten-rotation aggregate. The data had been examined in previous experiments; reshuffling does not make it historically pristine.

Every epoch evaluates both observed-history next-step prediction and full 90-step autonomous prediction.

**Checkpoint selection uses full autonomous validation error on water, dry fuel and gas only.**

Specifically:

- Normalized squared error.
- Average over the original three outputs and all 90 target samples.
- Equal configuration weighting.
- No active/quiet training weights.
- **Heating and gate-classification loss do not enter the checkpoint-selection objective.**

Heating does affect training; it does not directly decide which checkpoint is selected.

The best checkpoint updates on any lower validation score. The patience counter uses a larger “significant improvement” threshold: the greater of \(10^{-5}\) absolute or 0.1% relative. Patience resets at curriculum changes. Stopping requires at least 100 epochs and 30 stale epochs.

The actual gated run:

- **Trained for 213 epochs.**
- **Selected epoch 183.**
- **79,452 optimizer updates at the selected checkpoint.**
- **90,972 updates by the final epoch.**
- Stopped for validation patience.
- Selected normalized validation objective: approximately **0.0277731**.

I loaded the selected checkpoint and verified its model tensors exactly match the epoch-183 checkpoint.

The matched plain and gated selections were both frozen before either test evaluation. Every epoch’s checkpoint was retained. The output collection records 824 verified objects and the selection-before-test barrier. [Actual gated training report](/Users/wdavies/pi/wildfire3d/experiments/36_tree_density/data/pair-sequence-r0-results/fold01-report.json) · [Collection verification](/Users/wdavies/pi/wildfire3d/experiments/36_tree_density/results/pair-sequence-r0-collected.json)

**11. How the current full-sequence predictions are generated**

At the beginning, the actual initial state is repeated to fill the four-sample history:

```text
[S0, S0, S0, S0] → predict P1
[S0, S0, S0, P1] → predict P2
[S0, S0, P1, P2] → predict P3
[S0, P1, P2, P3] → predict P4
[P1, P2, P3, P4] → predict P5
...
```

Hidden memory starts at zero and carries continuously through all 90 predictions.

There are:

- No later simulation-state resets.
- No resetting memory every 16 or 32 steps.
- No online weight updates.
- No measured future heating or gas-release inputs.
- Continued access to the known conditions, ignition command and actual intervals.

The current full-sequence galleries use these saved autonomous predictions from the selected checkpoint. They do not rerun the model in the browser.

The **no-change line is a different comparator**, as you explicitly requested: at each target sample, it uses the actual preceding simulation state. Thus the baseline gets refreshed truth, while the model’s continuous trajectory does not.

The old rolling-horizon evaluation instead started at each origin with actual history and reconstructed actual-prefix memory, then forecast forward. That protocol produces different numbers and must not be presented as one uninterrupted trajectory. [Saved full-sequence data construction](/Users/wdavies/pi/wildfire3d/experiments/36_tree_density/model_evaluation/build_full_sequence.py:15)

**12. What this audit does—and does not—resolve**

This establishes the implemented architecture, its actual training procedure, the selected checkpoint, and how the published autonomous forecasts were produced.

It does **not** establish that:

- Four explicit samples or 32 memory values are sufficient.
- The memory has learned a physically meaningful temperature or combustion state.
- The gate thresholds are optimal.
- Thirty-two-step training adequately prepares it for 90-step prediction.
- The reduced four-variable representation is sufficient for general fire dynamics.
- Its behaviour is physically valid merely because it matches some FDS trajectories.

The simulations remain generic conical vegetation crowns with 1,600 weighted particles, a 0.5 m grid, and an imposed 1500°C ignition source for 20 seconds—not validated real trees, buildings, embers, or wildfire spread.

There are also stale descriptions in the saved files: the worker’s opening comment mentions “ten selections,” and the shared plan’s architecture text describes the **plain** arm. The actual executed loop has two arms and two selections; the gated code and recorded parameter count establish the gated architecture above. I have not silently repaired those descriptions during this audit.

**The central correction to my earlier explanations is precise: four explicit past samples, recurrent memory carried forward, and gradients through 1/8/16/32 predicted future steps. I must not describe any of those as an expanding 1/2/4/8/16 past-history window.**