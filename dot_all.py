import subprocess
import os

def run(cmd):
    subprocess.run(["powershell", "-Command", cmd])
  
if __name__ == '__main__':
	select_abst = input("Input abstraction: \'list\' / \'set\' ")
	select_k = input("Input k: ")

	if select_abst != "":
		absts = [select_abst]
	else:
		absts = ['list', 'set']

	if select_k != "":
		ks = [int(select_k)]
	else:
		ks = [3, 4, 5, 10, 15, 20]

	print(ks, absts)

	for abst in absts:
		for k in ks:
			for r in [-1, 500, 1000]:
				print(abst, k, r)
				if os.path.exists(f".\\{abst}{k}\\{r}\\ts_{abst}_{k}.dot"):
					run(f"cd .\\{abst}{k}\\{r}; rm *.png; ccomps -x .\\ts_{abst}_{k}.dot | dot -Grankdir=TB -Tpng -O; mv noname.gv.png {abst}_{k}_A.png; mv noname.gv.2.png {abst}_{k}_W.png; mv noname.gv.3.png {abst}_{k}_O.png")
# k = 3
# run("rm *.png")
# for abst in ['list', 'set']:
# 	run(f"ccomps -x .\\ts_{abst}_{k}.dot | dot -Grankdir=TB -Tpng -O; mv noname.gv.png {abst}_{k}_A.png; mv noname.gv.2.png {abst}_{k}_W.png; mv noname.gv.3.png {abst}_{k}_O.png")