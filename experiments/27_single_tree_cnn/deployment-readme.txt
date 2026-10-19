Single-tree conditional CNN, experiment27

Run: python predict.py --model cnn_32.pt --wind 3 --angle 90 --times 0,20,40,60,90,120,180 --out prediction.npz
Dependencies: NumPy and PyTorch. Tested versions are in ../../results/environment.json.
No FDS invocation or reference output is needed. CPU inference is the default.

Output axes: time, channel, X, Y, Z. Cell centers are0.25+0.5*i metres.
Channels: gas temperature Celsius, HRRPUV kW/m3, U/V/W velocity m/s, integrated radiation intensity kW/m2. Integrated intensity is NOT flux incident on a directed surface.
Domain24x16x16m. Wind is +X at1-5m/s. Angle is ignition arc azimuth:0deg downwind,180deg upwind. Requested physical time0-180s.

Supported canopy is fixed: generic cone radius1.5m, base2m, crown height8m, top10m. Frozen1600 vegetation particles; moisture0.12kg/kg dry. Artificial1500C stationary-particle ignition on60deg arc, radius1.2m,z2.1m, active0-20s. Bare nonflammable heatable ground. No trunks, buildings, ground fuel or embers.

This is a deterministic FDS surrogate, not physical validation or a calibrated probability model. No height/moisture/geometry variation, no neighboring-tree composition, no internal fuel/moisture prediction. See final experiment report for measured errors.
