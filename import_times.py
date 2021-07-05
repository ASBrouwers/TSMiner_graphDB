import pandas as pd
import os
from matplotlib import pyplot as plt

def create_plots(df):
	# ax = df.query("abst == 'list' and r == 1202267/16").plot('k', 'time', label='List-k-past',
	# 														 xlabel='Dataset size (rows)', ylabel='Time (s)')
	# df.query("abst == 'set' and r == 1202267/16").plot('k', 'time', ax=ax, label='Set-k-past')
	# plt.ylim(bottom=0)
	# plt.xlabel('Abstraction size (k)')
	# plt.show()
	# ax = df.query("abst == 'list' and k == 3").plot('r', 'time', label='List-k-past', xlabel='Dataset size (rows)',
	# 												ylabel='Time (s)')
	# df.query("abst == 'set' and k == 3").plot('r', 'time', ax=ax, label='Set-k-past', )
	# plt.ylim(bottom=0)
	# plt.xlabel('Dataset size (rows)')
	# plt.show()
	create_plot(df, "r == 1000", 'k', 'time', 'k', 'Time (s)', "", "k")
	create_plot(df, "k == 3", 'r', 'time', 'Dataset size (cases)', 'Time (s)', "", 3)
	create_plot(df, "k == 15", 'r', 'time', 'Dataset size (cases)', 'Time (s)', "", 15)

def create_plot(df, q, x, y, x_label, y_label, label, k):
	ax = df.query("abst == 'list' and " + q).plot(x, y, label=f"List-{k}-past", marker='o', figsize=(5, 4))
	df.query("abst == 'set' and " + q).plot(x, y, label=f"Set-{k}-past", ax=ax, marker='o')

	plt.ylim(bottom=0)
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.grid()
	plt.show()

def create_tables(df):
	print(df.query("abst == 'list' and k == 3").sort_values(by='r').to_latex(index=False, escape=False, header=["Abstraction", "$k$", "Cases", "Time (s)"], float_format="%.2f"))
	print(df.query("abst == 'set' and k == 3").sort_values(by='r').to_latex(index=False, escape=False,
																			header=["Abstraction", "$k$", "Cases",
																					"Time (s)"], float_format="%.2f"))
	print(df.query("abst == 'list' and r == 1000").sort_values(by='k').to_latex(index=False, escape=False,
																			 header=["Abstraction", "$k$", "Cases",
																					 "Time (s)"], float_format="%.2f"))
	print(df.query("abst == 'set' and r == 1000").sort_values(by='k').to_latex(index=False, escape=False,
																				 header=["Abstraction", "$k$", "Cases",
																						 "Time (s)"],
																				 float_format="%.2f"))

	print(df.query("abst == 'list' and k == 15").sort_values(by='r').to_latex(index=False, escape=False,
																			 header=["Abstraction", "$k$", "Cases",
																					 "Time (s)"], float_format="%.2f"))
	print(df.query("abst == 'set' and k == 15").sort_values(by='r').to_latex(index=False, escape=False,
																			header=["Abstraction", "$k$", "Cases", "Time (s)"], float_format="%.2f"))

if __name__ == '__main__':
	df = pd.DataFrame(columns=['abst', 'k', 'r', 'time'])
	for abst in ['list', 'set']:
		for k in [3, 4, 5, 10, 15, 20]:
			for r in [500,1000,2000,4000,8000]:
				if os.path.exists(f".\\{abst}{k}\\{r}\\ts_{abst}_{k}_time.txt"):
					with open(f".\\{abst}{k}\\{r}\\ts_{abst}_{k}_time.txt", 'r') as file:
						t = float(file.read().split()[0])
						df.loc[len(df.index)] = [abst, k, r, t]
						print(abst, k, r, t)

	# print(df)
	create_plots(df)
	create_tables(df)