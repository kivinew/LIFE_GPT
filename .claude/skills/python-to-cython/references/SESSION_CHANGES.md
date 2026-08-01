# Сводка изменений (сохранить перед компактификацией)

## sim_core.pyx изменения:
1. **Level-up масса и энергия**: threshold 50%, mass = 2.0 + level * 0.6, energy = 20% от новой max_e
2. **Combat reward**: x2.5 для ZOOP/POLY, diet_eff=0.85 для POLY
3. **Prey scan radius**: 6 ячеек (288px) вместо 2
4. **Chase logic**: относительное сравнение энергии (energies/my_max >= energies/prey_max)
5. **Stress response**: только для PHOT без активной реакции (не перед атакой)
6. **Level-based damage**: +30% урона за уровень (level_mult = 1 + level * 0.3)

## cell.py изменения:
1. **Divide threshold**: 30% вместо 95%
2. **Daughter properties**: random level 0..parent, mass 50% от max для уровня, energy 30%
3. **Random death on division**: до 5% для крупных клеток

## main.py изменения:
1. **HWSURFACE|DOUBLEBUF** в set_mode
2. **Sidebar reuse** вместо пересоздания каждый кадр
3. **Population mass display** в sidebar (A: 12 (48))