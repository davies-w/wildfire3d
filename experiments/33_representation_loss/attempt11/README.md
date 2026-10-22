# Attempt11: deterministic equivalent interpolation

Attempt10 failed before first optimizer update because CUDA trilinear interpolation backward has no deterministic implementation. Cleanup verified; reservation retained. This replacement keeps the same factor-two, align_corners=False trilinear rule using three separable dense matrix products. Real-arithmetic interpolation is equivalent; floating-point evaluation order differs. Synthetic forward/gradient checks compare original CPU operator; actual deterministic CUDA repeated-arm check remains mandatory. No changing mesh, resolution or loss to bypass failure.

Same four-arm comparison as10: encodedcontrol, dose_background, physical_low0.02, identical dose_repeat. Allcurrent6000 weights/optimizer independent deepcopies,2500updates/schedule3308; immutable saved optimizer hashes and exact finaldose/repeatweight equality. Previous optimizer-contamination suspicion withdrawn because existing roundtrip already isolates state. Run-to-run variation not conclusively attributed; this tests reproducibility.

Reserve2USD before submission within cumulative75cap. RegularL4us-central1-c; expected15–25min,20minqueue60mintask65minVM90minabsolute.500update checkpoints, newprefix/allowance for any recovery. No laptoptraining/newFDS. Same12train8strengthstratifieddevelopmentcases; not IID/pristinetest. Fullhistory original metrics/weakfires/background/tradeoffs retained;3frame loss not recurrence/fullhistorydose.

Generic3mwidecones4/6/8/10mabove2m,1600particles,.5m24x16x16m180s,1500C20s artificialsource,no trunks/buildings/embers,6gasfieldsnotgroundtemp. No physicalvalidation. Preserve DVC, code/workflowgenerators and publicarchive outputs.
