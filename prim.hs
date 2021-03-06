module Prim (
   prim,
   Edge(..)
) where

import Data.List(sort)
import Data.Set(member, notMember, empty, insert, singleton)

data Edge t = Edge t t Double deriving (Eq, Show)

instance Ord t => Ord (Edge t) where
   compare (Edge v1 v2 len1) (Edge v3 v4 len2) =
      compare (len1, min v1 v2, max v1 v2) (len2, min v3 v4, max v3 v4)

prim [] = []
prim edges = 
   let initialVertex ((Edge vertex _ _) : _) = vertex
       initialSet = singleton (initialVertex edges)
   in step (sort edges) initialSet []  

step [] _ solution  = solution
step edges vertices solution  =
   let (edge, newVertex) = findNextEdge edges vertices
       newVertices = insert newVertex vertices
       validEdge (Edge v1 v2 _) = notMember v1 newVertices || notMember v2 newVertices
       newEdges = filter validEdge edges
   in step newEdges newVertices (edge : solution)

findNextEdge [] vertices = error ("Disjunct graph with island " ++ show vertices)
findNextEdge (edge @ (Edge vertex1 vertex2 _) : edges) vertices
    | member vertex1 vertices = (edge, vertex2)
    | member vertex2 vertices = (edge, vertex1)
    | otherwise = findNextEdge edges vertices
                  
edges :: Edge                  
edges = (Edge 1 2 1.0)
                  
-- main :: IO()                  
-- main = print edges