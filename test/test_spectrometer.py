from hardware_comms.spectrometers.yokogawa import YokogawaOSA
import matplotlib.pyplot as plt
spec = YokogawaOSA("Yokogawa")

spec.active_trace = "TRG"
spec.set_trace_status({'mode': "WRITE"})
print(spec.sweep_parameters())
print(spec.read_trace_status())
# data = spec.spectrum()
# print(data[0])
# print(data[1])
# f, ax = plt.subplots(1,1)
# ax.plot(data[0],data[1])
# plt.show()
