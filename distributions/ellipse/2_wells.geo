zone producteur_1 {
  geometry = rectangle 180.00, 150.00, 6.00 5, 5, 12 m
  global-flux producteur_1
  geochem = aquifer
  source = -1 m3/h
}

zone injecteur_1 {
  geometry = rectangle 220.0, 150.0, 6.00 5, 5, 12 m
  global-flux injecteur_1
  geochem = aquifer
  source = 1 m3/h using leaching_solution_20
  modify at 30 days, source = 1 m3/h using leaching_solution
}