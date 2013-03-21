import Debug.Trace

--------------------------------------------------
-- Links
--------------------------------------------------

links_bidirectional = [
  (1,2),
  (1,5),
  (2,3),
  (2,6),
  (3,4),
  (3,8),
  (3,7),
  (4,8),
  (4,7),
  (5,6),
  (6,7),
  (7,8)
  ]
                      
links_unidirectional =                      
  links_bidirectional ++ reverse
  where
    reverse = map (\ (s,e) -> (e,s)) links_bidirectional
    
links = links_bidirectional  -- deprecated

--------------------------------------------------
-- Logic
--------------------------------------------------

maxInt :: Int
maxInt = maxBound::Int

-- Get the number of hops between a pair of cores
linkCost :: (Int, Int) -> Int
linkCost (x,y)
  | x == y     = trace ("linkCost eq with " ++ show (x,y)) (0)
  | otherwise  = trace ("linkCost other with " ++ show (x,y)) nb_min_costs_plus
  where 
    nb_min_costs_plus  | nb_min_costs == maxInt    = maxInt
                       | otherwise                 = nb_min_costs + 1
    nb_min_costs    | (length nb_costs) == 0    = maxInt
                    | otherwise                 = trace ("calculating minimum for list " ++ show nb_costs) minimum nb_costs -- get minimum of these costs
    nb_costs = trace ("calculating nb cost for " ++ show nb_list) (map linkCost nb_list) -- get cost of these links
    nb_list = trace ("getting nbs reached by links " ++ show nb ) (map (\ (s,e) -> (e,y)) nb) -- prepare input tuples for recursive call
    nb = filter ((==x).fst) links_unidirectional -- find links to neighbors

main :: IO()
main = print (linkCost (1,3))

--------------------------------------------------
-- Playground
--------------------------------------------------

skt :: (Int, Int) -> Int
skt (a,b) = b

-- Get the number of hops between a pair of cores
linkCostTest :: (Int, Int) -> IO()
linkCostTest (x,y) = print nb_list
  where 
    nb_list = map (\ (s,e) -> (e,y)) nb
    nb = filter ((==x).fst) links -- find links to neighbors


test :: IO()
test = print (length links_unidirectional)

