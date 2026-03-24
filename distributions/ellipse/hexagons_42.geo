zone producteur_1 {
  geometry = rectangle 107.50, 38.87, 6.00 5, 5, 12 m
  global-flux producteur_1 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_2 {
  geometry = rectangle 44.50, 75.25, 6.00 5, 5, 12 m
  global-flux producteur_2 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_3 {
  geometry = rectangle 170.50, 75.25, 6.00 5, 5, 12 m
  global-flux producteur_3 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_4 {
  geometry = rectangle 107.50, 111.62, 6.00 5, 5, 12 m
  global-flux producteur_4 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_5 {
  geometry = rectangle 233.50, 111.62, 6.00 5, 5, 12 m
  global-flux producteur_5 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_6 {
  geometry = rectangle 170.50, 147.99, 6.00 5, 5, 12 m
  global-flux producteur_6 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_7 {
  geometry = rectangle 296.50, 147.99, 6.00 5, 5, 12 m
  global-flux producteur_7 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_8 {
  geometry = rectangle 107.50, 184.37, 6.00 5, 5, 12 m
  global-flux producteur_8 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_9 {
  geometry = rectangle 233.50, 184.37, 6.00 5, 5, 12 m
  global-flux producteur_9 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_10 {
  geometry = rectangle 359.50, 184.37, 6.00 5, 5, 12 m
  global-flux producteur_10 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_11 {
  geometry = rectangle 170.50, 220.74, 6.00 5, 5, 12 m
  global-flux producteur_11 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_12 {
  geometry = rectangle 296.50, 220.74, 6.00 5, 5, 12 m
  global-flux producteur_12 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_13 {
  geometry = rectangle 233.50, 257.11, 6.00 5, 5, 12 m
  global-flux producteur_13 
  geochem = aquifer
  source = -12 m3/h
}

zone producteur_14 {
  geometry = rectangle 359.50, 257.11, 6.00 5, 5, 12 m
  global-flux producteur_14 
  geochem = aquifer
  source = -12 m3/h
}

zone injecteur_1 {
  geometry = rectangle 65.50, 38.87, 6.00 5, 5, 12 m
  global-flux injecteur_1 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_2 {
  geometry = rectangle 149.50, 38.87, 6.00 5, 5, 12 m
  global-flux injecteur_2 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_3 {
  geometry = rectangle 86.50, 75.25, 6.00 5, 5, 12 m
  global-flux injecteur_3 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_4 {
  geometry = rectangle 128.50, 75.25, 6.00 5, 5, 12 m
  global-flux injecteur_4 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_5 {
  geometry = rectangle 212.50, 75.25, 6.00 5, 5, 12 m
  global-flux injecteur_5 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_6 {
  geometry = rectangle 65.50, 111.62, 6.00 5, 5, 12 m
  global-flux injecteur_6 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_7 {
  geometry = rectangle 149.50, 111.62, 6.00 5, 5, 12 m
  global-flux injecteur_7 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_8 {
  geometry = rectangle 191.50, 111.62, 6.00 5, 5, 12 m
  global-flux injecteur_8 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_9 {
  geometry = rectangle 275.50, 111.62, 6.00 5, 5, 12 m
  global-flux injecteur_9 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_10 {
  geometry = rectangle 86.50, 147.99, 6.00 5, 5, 12 m
  global-flux injecteur_10 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_11 {
  geometry = rectangle 128.50, 147.99, 6.00 5, 5, 12 m
  global-flux injecteur_11 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_12 {
  geometry = rectangle 212.50, 147.99, 6.00 5, 5, 12 m
  global-flux injecteur_12 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_13 {
  geometry = rectangle 254.50, 147.99, 6.00 5, 5, 12 m
  global-flux injecteur_13 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_14 {
  geometry = rectangle 338.50, 147.99, 6.00 5, 5, 12 m
  global-flux injecteur_14 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_15 {
  geometry = rectangle 149.50, 184.37, 6.00 5, 5, 12 m
  global-flux injecteur_15 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_16 {
  geometry = rectangle 191.50, 184.37, 6.00 5, 5, 12 m
  global-flux injecteur_16 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_17 {
  geometry = rectangle 275.50, 184.37, 6.00 5, 5, 12 m
  global-flux injecteur_17 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_18 {
  geometry = rectangle 317.50, 184.37, 6.00 5, 5, 12 m
  global-flux injecteur_18 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_19 {
  geometry = rectangle 212.50, 220.74, 6.00 5, 5, 12 m
  global-flux injecteur_19 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_20 {
  geometry = rectangle 254.50, 220.74, 6.00 5, 5, 12 m
  global-flux injecteur_20 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_21 {
  geometry = rectangle 338.50, 220.74, 6.00 5, 5, 12 m
  global-flux injecteur_21 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_22 {
  geometry = rectangle 275.50, 257.11, 6.00 5, 5, 12 m
  global-flux injecteur_22 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

zone injecteur_23 {
  geometry = rectangle 317.50, 257.11, 6.00 5, 5, 12 m
  global-flux injecteur_23 
  geochem = aquifer
  source = 7.304347826086956 m3/h using leaching_solution_20
  modify at 30 days, source = 7.304347826086956 m3/h using leaching_solution
}

