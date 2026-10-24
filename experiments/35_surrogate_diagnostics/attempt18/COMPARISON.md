## Completed matched MLP versus GRU comparison (attempts16–18)

All20 validation-selected models were frozen before held-out testing. All520 histories/480 configurations contributed through grouped ten-fold8/1/1 rotations; replicas remained together. Tests were previously examined and explicitly reshuffled. The continuation restored the actual epoch373 model, optimizer and random-number states on GPU before fitting. No scientific settings changed.

Exactly three evolving outputs: derived remaining water kg, unreacted dry vegetation kg, vegetation fuel-gas release kg/s. Both use21 measured inputs (four three-state frames plus nine known forcing/static values). The GRU has32 internal memory values, not extra physical inputs.

| Forecast horizon | MLP water / dry fuel / release error % | GRU water / dry fuel / release error % |
|---|---|---|
| 2s | 0.76 / 0.97 / 28.39 | 0.75 / 0.76 / 25.97 |
| 8s | 2.61 / 2.57 / 50.18 | 2.40 / 2.39 / 41.78 |
| 16s | 4.63 / 4.39 / 59.48 | 4.18 / 4.12 / 47.43 |
| 32s | 7.24 / 6.67 / 64.44 | 6.43 / 6.42 / 56.04 |
| 90s | 14.32 / 12.93 / near-zero denominator | 12.26 / 13.87 / near-zero denominator |

Equal mean of ten folds; each fold is configuration-balanced. Percentage error = aggregate MAE / aggregate mean absolute true endpoint state, not mean per-case percentage.

Forecasts start at every valid observed origin and feed predictions back thereafter. A90s forecast endpoint lies in the near-inactive latter half of these simulations; release percentage error is misleading because the true mean is approximately0.00000195kg/s. At90s, release MAE is0.000529kg/s MLP versus0.000426kg/s GRU; this is not evidence of90seconds of sustained-burning accuracy.

At16s, GRU reduces error versus matched MLP by9.7%water,6.2%dryfuel,20.3%release; against no-change by62.3%,61.0%,72.1%. Release improves in all ten folds at2/8/16/32s. At90s, GRU water error improves14.4% but dryfuel error worsens7.3% (only2/10folds improve).

Full180s autonomous rollout from the initial state is a separate measure: MLP MAE0.699kgwater/4.150kgdryfuel/0.05562kg/srelease; GRU0.651/3.800/0.04958, improvements6.8%/8.4%/10.9%. Memory helps modestly; it does not remove drift. Negative release occurs in37.5% of GRU rollout outputs, with average negative magnitude0.000161kg/s over all outputs; water negativity and accumulated mass increases also remain. No physical clipping was used.

Seventeen runs stopped by validation patience; three reached400epochs, not demonstrated convergence. Early stopping is evidence about this validation criterion, not proof of an optimization optimum. No new training is launched from these test results.

All1,513 new output files verified, all prior attempt16 checkpoints retained. PublicDVC archive verified54,318 object paths/sizes and six anonymous SHA256 downloads; this is not a complete remote-byte rehash. VM/job/disks empty and exact temporary grant removed. Attempt18 measured-runtime compute estimate$0.3794; whole-project estimate$21.0066, not an invoice. Code and workflow generators are pushed on codex/ignition-surrogate-pilot.

Scope remains derived water/fuel and fuel-gas release, with char treated as inert ash and0.75fuel-gas yield. Generic3m-wide crowns4/6/8/10m above2m,1600weightedparticles,.5m mesh24×16×16m,180s,1500°C artificial20s source, no trunks/buildings/embers;48legacy cases have documented geometry differences. This does not measure heat release or plume physics.
