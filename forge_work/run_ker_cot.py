
def rc(vp1, rho1, vp2, rho2):
    ai1 = vp1 * rho1
    ai2 = vp2 * rho2
    return (ai2 - ai1) / (ai2 + ai1)

# End members
# Serpentinite: Vp 5.5-6.5 (avg 6.0), rho 3100-3250 (avg 3175)
# Hyperextended crust: Vp 6.0-6.5 (avg 6.25), rho 2700-2900 (avg 2800)
# True oceanic: Vp 6.8-7.2 (avg 7.0), rho 2900-3000 (avg 2950)
# PSCS slab: Vp 7.0-7.5 (avg 7.25), rho 3200-3300 (avg 3250)

print("Serpentinite / hyperextended crust:", rc(6.0, 3175, 6.25, 2800))
print("Hyperextended crust / true oceanic:", rc(6.25, 2800, 7.0, 2950))
print("Serpentinite / PSCS slab:", rc(6.0, 3175, 7.25, 3250))
print("Hyperextended crust / PSCS slab:", rc(6.25, 2800, 7.25, 3250))
print("True oceanic / PSCS slab:", rc(7.0, 2950, 7.25, 3250))

# KT-7 Franke Vp=6.4 km/s.
# Let's say upper is hyperextended crust Vp=6.0, rho=2700. Lower is Serpentinite Vp=6.4, rho=3175.
print("KT-7 Hyperextended to Serpentinite (Vp=6.4, rho=3175):", rc(6.0, 2700, 6.4, 3175))
