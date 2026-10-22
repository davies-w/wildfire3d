# Experiment 33 — spatial representation and loss diagnostic

Submitted as gpu33-pilot01. Synthetic forward/loss/source-removal checks pass. No laptop training or new FDS runs.

Compare 600 additional updates (three consecutive frames each) on 12 existing training configurations and eight separate development-validation configurations:

1. Saved experiment32 snapshot model with original loss.
2. Same saved initialization with balanced hot/background, total-strength, spatial-allocation, radiation, airflow and temporal-difference losses.
3. New spatial density/ignition input model with independent temperature, combustion, radiation and airflow decoders; positive total combustion allocated over a normalized spatial field; revised losses.

All arms share a fixed configuration/time-window schedule. The new architecture starts from scratch; the other arms have prior training. This is a capacity diagnostic, not an equal-total-training architecture comparison. Cases were deliberately stratified by development fire strength and height, not randomly sampled for an IID score. No former fresh-test outputs are ingested. The model remains a snapshot predictor with a temporal-difference loss; it is not recurrent.

Full 180-second histories are evaluated before/after training on each case. Preserve original physical metrics and report percentage errors, weak-burning behavior and cold-background errors separately. Do not decide success from the training objective alone. Improvement on these deliberately selected cases warrants a full-development comparison, not a claim of generalization or physical accuracy. Previously examined test cases cannot serve as a new untouched test.

## Runtime and spending

User approved a cumulative $35 cap; $24.60 prior reservations retained and $1.50 reserved for this pilot ($26.10 total). Pilot allowance $1.50; estimate $0.40–$0.90, approximately 20–45 minutes after provisioning, uncertain until spatial-model throughput is measured. Existing experiment32 reservations remain $24.60 against its $25 cap. Reservation recorded before upload and submission in budget.json.

Prepared Spot L4 workflow: zero automatic retries, 60-minute task limit, 65-minute VM-age limit, 90-minute absolute deadline including queue, 20-minute queue limit and cloud-side deletion. Reserve the full $1.50 before submission, including ancillary/cleanup allowance. Upload checkpoints every100 updates. Worker supports explicit checkpoint restoration and gates training with a CUDA serialization/forward replay check. This checks restoration, not bitwise equality of an additional optimizer step. Interrupted checkpoints must be retained; any replacement needs a separate reservation and new output prefix. launch.py reserves before submission; collect.py preserves outputs and removes the temporary exact-object read grant after terminal cleanup.

## Data limitations

Reuses generic single conical crowns, 3m wide and 4/6/8/10m high above a 2m base, fixed1600 weighted vegetation samples. Domain24×16×16m, uniform0.5m cells,180s. Artificial1500°C particles impose ignition for20s. Wind1/3/5m/s along+X; moisture0.06–0.30 dry basis; loading multipliers0.7/1/1.3. No trunks, buildings or embers. Bare nonflammable ground is heatable in FDS, but solid-ground temperature is not a learned output. Six learned gas fields: temperature, combustion heat-release density, three velocity components and radiation. No claim of real-world validation.

Run setup.py, validate.py and prepare_pilot.py locally; worker.py is CUDA-only. Preprocessing verifies existing raw, deck, checkpoint and density hashes before learning. Frozen input hashes and prepared workflow are under results/ and gpu-workflow.yaml.

## Pilot01 outcome and follow-up

Completed and collected; VM/job/disk cleanup verified and temporary input permission removed. Median post-source validation hot-temperature relative error improved66.77%→57.26% with revised loss, but heat-release63.81%→73.88% and radiation61.61%→68.33% worsened. Current-loss extra updates gave64.14%,73.05%,69.76%. New spatial model after600updates remained at98.80%,93.02%,97.32%, respectively. Do not interpret its low whole-volume error as successful fire prediction: near-ambient predictions can improve that metric while missing fire. Full per-arm/per-case evidence is results/report.json; summarized in results/summary.json.

Attempt02 continues all three arms from their600-update checkpoints to6000 total updates using unchanged models/losses and the same deterministic schedule prefix. This tests whether the fresh model's short training was insufficient before modifying the objective again. Same12train/8validation configurations; no expansion or new FDS. Separate$1.50 reservation, retained pilot01 allowance, cumulative$27.60 if submitted. Actual pilot01 worker learning/evaluation took about162s plus preprocessing/provisioning, much faster than estimate. Allow10–25minutes for attempt02 including provisioning/preprocessing, with the same60min task/65min VM/90min absolute limits. Checkpoint uploads every500updates; the initial600-step checkpoints remain preserved.

Attempt02 was reclaimed by Spot (Batch exit50001) after the current arm uploaded its6000-step checkpoint. No final comparison exists for that attempt. Cleanup/permission removal verified. Attempt03 is a separately reserved$1.50 replacement, retaining previous reservations; resumes current at6000 and the other arms at600, without changing objectives. Cumulative reserved$29.10.

Attempt03 completed; cleanup/permission removal verified. At6000updates median validation temperature/heat-release/radiation errors were66.27/58.99/61.10% current,63.55/74.04/71.95% revised-loss,99.99/431.36/82.26% spatial. Spatial training temperature also99.98%, so there is a capacity/optimization failure rather than just unseen-case generalization. Revised loss reduced whole-volume temperature-rise error415.43→110.00% but did not improve all quantities. These medians are over the deliberately stratified development subset.

Attempt04 targets the loss: per-frame hot/bright squared encoded errors,0.1 background weighting, smooth log-total-strength and KL allocation replace the previous loss. Current6000 model fixed; loss_only/spatial continue6000→12000. Hypothesis of competing background/weak-fire gradients is unproven; compare measured outcomes before expanding data. New$1.50 reservation, cumulative$30.60. All prior results/checkpoints retained. Attempt03 report initial rows evaluate original weights before restoring checkpoints: use final rows across attempts for comparisons.

Attempt04 Spot VM was reclaimed before task startup (exit50001,runDuration0s); no scientific result. Cleanup and permission removal verified. Attempt05 reuses identical checkpoint/loss setup on a regular L4 VM (quota confirmed), with separately reserved$2 full allowance; cumulative$32.60, leaving$2.40. Retain all previous reservations. Same deadlines/checkpoints. This avoids Spot reclamation but does not guarantee capacity/startup or eliminate other failures.

Attempt05 at05:30UTC remained scheduled: us-central1-a resource pool exhausted, no task startup. Existing20min queue deadline and collector remain active; no duplicate job. Forward-only saved-weight diagnostic on first3training cases at30/90s found temperature output clamp fraction0%; this excludes clamp saturation only for those samples. Diagnostic code/results retained.
