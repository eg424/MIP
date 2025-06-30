import magpylib as magpy
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.transform import Rotation as R
import math
# 线圈参数
hx_current =1 # 电流强度 (A)
hx_diameter = 0.1  # 线圈直径 (m)
hx_distance = 0.05 
hx_turns = 100

mx_current = 3.5  # 电流强度 (A)
mx_diameter = 0.104  # 线圈直径 (m)
mx_distance = mx_diameter/2 * math.sqrt(3)
mx_turns = 100

my_current = 1  # 电流强度 (A)
my_diameter = 76.21*2/1000  # 线圈直径 (m)
my_distance = 0.132
my_turns = 152


hy_current = 1  # 电流强度 (A)
hy_diameter = 88*2/1000  # 线圈直径 (m)
hy_distance = 0.088
hy_turns = 176

mz_current = 3.5  # 电流强度 (A)
mz_diameter = 0.25  # 线圈直径 (m)
mz_distance = mz_diameter/2 * math.sqrt(3)
mz_turns = 1200

# mx_current = 3.5  # 电流强度 (A)
# mx_diameter = 0.2  # 线圈直径 (m)
# mx_distance = mx_diameter/2 * math.sqrt(3)
# mx_turns = 5000


x_orientation = R.from_euler('xyz', [0, 90, 0], degrees=True)  # 绕 y 轴旋转 90 度
y_orientation = R.from_euler('xyz', [90, 0, 0], degrees=True)  

coil_hx1 = magpy.current.Circle(position=(-hx_distance/2, 0, 0), orientation=x_orientation, diameter=hx_diameter, current=hx_current)
coil_hx2 = magpy.current.Circle(position=(hx_distance/2, 0, 0), orientation=x_orientation, diameter=hx_diameter, current=hx_current)

coil_mx1 = magpy.current.Circle(position=(-mx_distance/2, 0, 0), orientation=x_orientation, diameter=mx_diameter, current=mx_current)
coil_mx2 = magpy.current.Circle(position=(mx_distance/2, 0, 0), orientation=x_orientation, diameter=mx_diameter, current=-mx_current)

coil_hy1 = magpy.current.Circle(position=(0, -hy_distance/2, 0), orientation=y_orientation, diameter=hy_diameter, current=-hy_current)
coil_hy2 = magpy.current.Circle(position=(0, hy_distance/2, 0), orientation=y_orientation, diameter=hy_diameter, current=-hy_current)

coil_my1 = magpy.current.Circle(position=(0, -my_distance/2, 0), orientation=y_orientation, diameter=my_diameter, current=my_current)
coil_my2 = magpy.current.Circle(position=(0, my_distance/2, 0), orientation=y_orientation, diameter=my_diameter, current=-my_current)


# 创建一个传感器并沿 x 轴放置多个位置
pos = 0.024
x_positions = np.linspace(-pos, pos, 100)  # 从 -0.2 m 到 0.2 m 的 100 个位置
B_hx_list = []
B_mx_list = []
B_x_list = []
for x in x_positions:
    B_hx = coil_hx1.getB([x, 0, 0]) + coil_hx2.getB([x, 0, 0]) 
    B_hx_list.append(B_hx[0]*1000*hx_turns)
    B_mx = coil_mx1.getB([x, 0, 0]) + coil_mx2.getB([x, 0, 0]) 
    B_mx_list.append(B_mx[0]*1000*mx_turns)
    B_x_list.append(B_hx[0]*1000*hx_turns + B_mx[0]*1000*mx_turns)

      
pos = 0.024
y_positions = np.linspace(-pos, pos, 100)  # 从 -0.2 m 到 0.2 m 的 100 个位置
B_hy_list = []
B_my_list = []
B_y_list = []

t = coil_hy1.getB([0,0,0])*1000*hy_turns


for y in y_positions:
    B_hy = coil_hy1.getB([0, y, 0]) + coil_hy2.getB([0, y, 0]) 
    B_hy_list.append(B_hy[1]*1000*hy_turns)
    B_my = coil_my1.getB([0, y, 0]) + coil_my2.getB([0, y, 0]) 
    B_my_list.append(B_my[1]*1000*my_turns)
    B_y_list.append(B_hy[1]*1000*hy_turns + B_my[1]*1000*my_turns)


fig = plt.figure(figsize=(10, 4))

# 2D 绘图
ax1 = fig.add_subplot(121)
ax1.plot(x_positions, B_mx_list)
ax1.set_title("Magnetic Field $B_x$ along x-axis (Helmholtz Coils)")
ax1.set_xlabel("Position along x-axis (m)")
ax1.set_ylabel("Magnetic Field $B_x$ (mT)")

# 3D 绘图
ax2 = fig.add_subplot(122, projection="3d")

# 显示线圈和磁场
magpy.show(coil_hx1, coil_hx2, coil_mx1,coil_mx2, coil_my1, coil_my2,coil_hy1,coil_hy2,canvas=ax2)

# 添加 x 轴方向的辅助线
ax2.plot([-.2, .2], [0, 0], [0, 0], color='k')

# 生成图像
plt.tight_layout()
# plt.show()

Bx_grad = (B_mx_list[-1]-B_mx_list[0])/(2*pos)
By_grad = (B_my_list[-1]-B_my_list[0])/(2*pos)
# print(By_grad)
print("bx_grad:")
print(Bx_grad/1000)
B_aix = 0.060 
d = 24e-3 #m
t_total = 24 #s
v = d / t_total

dt = 0.01
a = v/dt

r = 5e-4
m = 7500 * 4 / 3 * math.pi * (r**3)
g = 9.8
Fg =  m * g

rho_fluid = 968
nu = 350e-6 
eta_silicone_oil = nu * rho_fluid

F_drag = 6*math.pi*eta_silicone_oil*r*v
V = (4 / 3) * math.pi * r ** 3  # 球体积，m^3
F_b = rho_fluid*g*V
print(f'F_b is {F_b}')

Fm = m*a + Fg + F_drag - F_b
print("mm_agent")
print(Fm)
mu_0 = 4 * math.pi * 1e-7 
M = B_aix / mu_0 *3/2 # 磁化强度，A/m

mm_agent = M * V  # 磁矩，A·m^2

gradient = Fm/mm_agent
print("gradient")
print(gradient)
I = 3.5

r = 5e-4 *2
# r = 1e-4
mz_r = 0.104
N = 1200
A = math.pi * r**2
print(A)
L = 2* math.pi *mz_r*N
print(L)
V = A*L
print(V)
m = 8960 * V
c = 385
R_4 =1.68e-8 * L/A

print(R_4)

unit_gradient = gradient / I

T = 600 #s

Q = I**2 * R_4 *T
print(Q)

delta_T = Q/(m*c)

print(delta_T)


delta_T = (I**2)/(r**4) * T * 1.68e-8 / ((math.pi**2) * c*8960)
print(delta_T)
h = 10
A_h = 2* math.pi *mz_r * 50e-3

delta_T = Q /( m*c + h*A_h*T)

print(delta_T)
# import math

# def calculate_B_z(mu_0, I, R, z):
#     """Calculate the magnetic field B_z on the axis of a circular loop of current."""
#     B_z = (mu_0 * I * R**2) / (2 * (R**2 + z**2)**(3/2))
#     return B_z

# # Constants and parameters
# mu_0 = 4 * math.pi * 10**-7  # Vacuum permeability in T·m/A
# I = 5  # Current in A
# R = 0.1  # Radius of the coil in m
# z = 0.1  # Distance on the axis from the center in m

# # Calculate the magnetic field B_z
# B_z = calculate_B_z(mu_0, I, R, z)
# print(B_z)