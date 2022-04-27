from data import *

filename = "pep_ko_ivv.csv"
n = 7
k = 0.5
stock_a = 'pep'
stock_b = 'ko'

lmt_priceA = 'N/A'
lmt_statusA = 'Filled'
lmt_priceB = 'N/A'
lmt_statusB = 'Filled'

trip = "Entry"

sizeA = sizeB = 1000

# data & table
# all_data = get_full_signal(file_name, moving_average_num, std_level, stockA, stockB)
entry_blotter = calculate_entry_orders(filename, n, k, stock_a, stock_b,
                                       sizeA, sizeB, trip, lmt_priceA,
                                       lmt_statusA, lmt_priceB, lmt_statusB)

entry_blotter = entry_blotter.set_index("DATE")
entry_blotter.to_csv('entry_blotter.csv')
