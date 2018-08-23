
from pulp import *
import itertools
from collections import defaultdict


class validPath:
    """
        This class defines a valid path, i.e., one vertex per day.
        
        A vertex (or route) corresponds to a set of clients.
        The cost of a path is number of distinct clients involved in the path,
        that is the cardinality of the union of the sets of clients associated to each vertex.
        """
    
    def __init__(self, name, routeList = []):   # i've changed the input on routelist from [] to dict {}
        """
            INPUT:
            - ``name`` is the id of the path
            - ``routeList`` is the list of routes in the path. A route is represented as the set of clients it contains.
            """
        self.name = name
        self.path = routeList
        
        newSet = set()
        
        # route = list of clients, node in graph
        # routeList = list of routes, path of a driver for all days
        for route in routeList:
            newSet = newSet.union(route)
        
        self.totalClients = len(newSet)
    
    def __str__(self):
        return self.name


Clients = 9
client_list = [1,2,3,4,5,6,7,8,9]
totalNumberOfDays = 2
day_list = [0,1]
totalNumberOfDrivers = 3
driver_list = [0,1,2]
indexesOfRoutes_List = [0,1,2]



def route_in_validPath(validPath, inputDict, driver, day):
    """
        Check if the ith route of day is in the validPath.
        
        INPUT:
        - ``validPath`` -- a valid path for a driver
        - ``inputDict`` -- dictionary keyed by days, containing the list of routes of each day
        - ``driver`` -- index of the route to check
        - ``day`` -- day to consider
        
        """
    #return (inputDict[day][i] in validPath.path)    # output 1, if node exists in the input dicts
    return (inputDict[day][driver] == validPath.path[day])


def masterSolve(validPaths, inputDict, relax=True):
    """
        (Relaxed) Master Problem: Select best subset of validPath among the current list of valid paths (validPaths).
        
        INPUT:
        - ``validPaths`` -- current list of validPaths P_i, indexed by name
        - ``inputDict`` -- dictionary keyed by days, containing the list of routes of each day
        - ``relax`` -- (default: True) whether to solve the relaxed master problem or the ILP.
        """
    
    # The variable 'prob' is created
    prob = LpProblem("Consistency", LpMinimize)
    
    # vartype represents whether or not the variables are relaxed
    if relax:
        vartype = LpContinuous
    else:
        vartype = LpInteger

    # The problem variables are created
    pathVars = LpVariable.dicts("validPath", validPaths, 0, 1, vartype)
    # pathVars : dictionary of variables, indexed by validPath_name


    # Set the objective function
    prob += lpSum([path.totalClients * pathVars[path] for path in validPaths])

    # Each (route, day) must be covered by a path 
    cnt = 0
    for r in range(totalNumberOfDrivers):
        for j in range(totalNumberOfDays):
            prob += lpSum([(pathVars[path]*(route_in_validPath(path,inputDict,r,j)) for path in validPaths)]) >= 1,"Min%s"%cnt
            cnt += 1


    prob.solve()
    
    prob.roundSolution()
    
    
    cnt = 0
    if relax:
        duals = defaultdict(dict)
        for r in range(totalNumberOfDrivers):
            for j in range(totalNumberOfDays):
                name = 'Min'+str(cnt)
                duals[j][r] = prob.constraints[name].pi
                cnt += 1
    
    
        for j in day_list:
            for r in driver_list:
                print j,r,duals[j][r]

                    return duals

    else:
        solution = []
        for p in validPaths:
            if (pathVars[p].varValue > 0):
                solution.append(p.path)


    return value(prob.objective), solution



def subSolve(inputDicts, validPaths, duals):
    """
        Pricing problem: search for a validPath with negative reduced cost.
        
        INPUT:
        - ``validPaths`` -- current list of valid paths
        - ``duals`` -- dictionary keyed by (day, route), containing the value of the dual variables associated to the constraints of the master problem
        """
            
        prob = LpProblem("SubProb", LpMinimize)
                
        clients_in_path = LpVariable.dicts("Clients", client_list, 0, 1, LpInteger)
                    
        route_in_path = LpVariable.dicts("route_in_path",(day_list, indexesOfRoutes_List), 0, 1, LpInteger)
                            
                            
        prob += (lpSum([clients_in_path[c] for c in client_list]) - lpSum([route_in_path[j][r]*duals[j][r] for j in day_list for r in indexesOfRoutes_List])),"Objective"
                                
        # Constraints
        for j in range(totalNumberOfDays):
            prob += lpSum([route_in_path[j][r] for r in indexesOfRoutes_List]) == 1,"oneRoutePerDay%s"%j
                                        
        count = 0
        """
            for c in client_list:
                for j in range(totalNumberOfDays):
                        for r in indexesOfRoutes_List:
                            if (c in inputDicts[j][r]):
                                prob += (clients_in_path[c] >= route_in_path[j][r]),"clientsInRoutesUsed%s"%count
                                count += 1
        """
        for j in range(totalNumberOfDays):
            for r in indexesOfRoutes_List:
                for c in inputDicts[j][r]:
                    prob += (clients_in_path[c] >= route_in_path[j][r]),"clientsInRoutesUsed%s"%count
                    count += 1
                                                                    
        prob.solve()
                                                                        
        prob.roundSolution()
                                                                            
        varsdict = {}
        newPath = []
             
        for v in prob.variables():
            varsdict[v.name] = v.varValue
                     
        for j in range(totalNumberOfDays):
            for r in indexesOfRoutes_List:
                variable_name = 'route_in_path_'+str(j)+'_'+str(r)
                    if (varsdict[variable_name]):
                        newPath.append(inputDicts[j][r])
                                         
         print ("New Path = {}".format(newPath))
                                             
         print ("Objective = {}".format(value(prob.objective)))
                                                 
         if value(prob.objective) < -10**-5:
            morePaths = True    # continue adding paths
            validPaths.append(validPath("P"+str(len(validPaths)), newPath))
         else:
             morePaths = False
                                                                     
                                                                     
         return validPaths, morePaths
                                                                                    



#inputDicts = {0: [{1,2,3},{4,5,6},{7,8,9}], 1: [{4,6,7},{1,2,9},{3,5,8}], 2: [{2,3,5},{4,7,8},{1,6,9}], 3: [{1,7,8,9}, {2,3,6}, {4,5}]}
inputDicts = {0: [{1,2,3},{4,5,6},{7,8,9}], 1: [{4,6,7},{1,2,9},{3,5,8}]}


morePaths = True

#pathList = {0: [{1,2,3},{1,2,9},{4,7,8},{1,7,8,9}], 1:[{4,5,6},{3,5,8},{1,6,9},{4,5}], 2:[{7,8,9},{4,6,7},{2,3,5},{2,3,6}]}
pathList = {0: [{1,2,3},{1,2,9}], 1:[{4,5,6},{3,5,8}], 2:[{7,8,9},{4,6,7}]}

Paths = []


for i in range(totalNumberOfDrivers): 
    Paths.append(validPath("P"+str(i), pathList[i]))


while morePaths:
    
    # Solve problem as a relaxed LP
    duals = masterSolve(Paths, inputDicts)
    
    # Find another Path
    Paths, morePaths = subSolve(inputDicts, Paths, duals)



# Re-solve as an integer problem
objective, solution = masterSolve(Paths, inputDicts, relax = False)


# Display Solution
print solution

print("objective = ", objective)
