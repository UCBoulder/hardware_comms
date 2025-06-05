from hardware_comms.spectrometers.yokogawa import YokogawaOSA
import matplotlib.pyplot as plt
spec = YokogawaOSA("Yokogawa")

spec.active_trace = "TRG"
spec.active_trace_status= "WRITE"
spec.resolution = 1

print(spec.sweep_parameters())
spec.get_new_single()
data = spec.spectrum()
# print(data[0])
print(data[1])
# f, ax = plt.subplots(1,1)
# ax.plot(data[0],data[1])
# plt.show()
