'''This file is part of AToMPM - A Tool for Multi-Paradigm Modelling
Copyright 2011 by the AToMPM team and licensed under the LGPL
See COPYING.lesser and README.md in the root of this project for full details'''

'''
Transformation context for MDE
Author: Mohanad Alsharef (mohanad)
Purpose: MDE integration to AtomPM
'''
import random
import collections
import datetime
from time import *
import timeit
from .pytcore.tcore.messages import Pivots
from .tconstants import TConstants as TC
from .utils import Utilities as utils
from .tcontext import TransformationContext
from .pytcore.rules.srule import SRule
from .pytcore.rules.arule import ARule
from .pytcore.rules.query import Query

class MdeContext(TransformationContext) :
    def __init__(self,fname,ptcal):
        super(MdeContext,self).__init__(ptcal._transfData[fname])
        self.fname = fname
        self.metamodel = TC.MDE
        self.birdmodel = '/Formalisms/Bird/Bird'
        self.compiler = ptcal._compiler
        self.ptcal = ptcal
        self.highlight = ptcal._requestNodeHighlight
        self.haswid = ptcal._aswCommTools['wid']
        self.sendAndApplyDeltaFunc = ptcal.sendAndApplyDelta
        self.totalExecutionTime=0
        self.rules={}
        self.nextInput = "packetIn"

        self.startStateID = None
        self.lastNode= 0 # used to know the last node id and start the nodes for the patterns after the last node
        self.MazePosition = 650
        self.mazeNodesId =[]
        self.birdMazeFacing= ''
        self.ruleBirdNodesId=[]
        self.ruleId=[]
        self.queryId=[]

        '''
        Identify items in canvas and make lists of input side and transformation side
        '''
        for id in self.t['nodes']:
            self.lastNode = int(id)
            if int(id) > self.lastNode:
                self.lastNode = int(id)
            if self.t['nodes'][id]['$type'] == self.metamodel+"/Start":
                self.startStateID = id
                self.highlight(
                            '127.0.0.1:8124',
                            self.haswid,
                            self.startStateID)
            elif self.t['nodes'][id]['$type'] == self.metamodel+"/Query":
                self.ruleId.append(id)
            elif self.t['nodes'][id]['$type'] == self.metamodel+"/Rule":
                self.ruleId.append(id)
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/Empty":
                if self.t['nodes'][id]['position']['value'][0] < self.MazePosition:
                    self.mazeNodesId.append(id)
                else:
                    self.ruleBirdNodesId.append(id)
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/Tile":
                if self.t['nodes'][id]['position']['value'][0] < self.MazePosition:
                    self.mazeNodesId.append(id)
                else:
                    self.ruleBirdNodesId.append(id)
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/Bird":
                if self.t['nodes'][id]['position']['value'][0] < self.MazePosition:
                    self.mazeNodesId.append(id)
                    self.birdMazeFacing= self.t['nodes'][id]['facing']['value']
                else:
                    self.ruleBirdNodesId.append(id)
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/Pig":
                if self.t['nodes'][id]['position']['value'][0] < self.MazePosition:
                    self.mazeNodesId.append(id)
                else:
                    self.ruleBirdNodesId.append(id)
        
        '''
        Creating rules list
        '''
        for r in self.ruleId:
            if self.t['nodes'][r]['name']['value'] == '':
                self.t['nodes'][r]['name']['value'] = 'ruleIdNum'+str(r)
            self.rules[r] = {'id':r,
                                    'name':self.t['nodes'][r]['name']['value'],
                                    'alias':'',
                                    'rule':self.createCompiledRules(r)}
        
        
    
    def createCompiledRules(self,ruleId):
        if self.t['nodes'][ruleId]['$type'] == self.metamodel+"/Rule":
            maxIterations = self.t['nodes'][ruleId]['count']['value']
            ruleTranslatedPattern = self.createRulePattern(ruleId)
            ruleName = '/Formalisms/Bird/R_ruleIdNum'+str(ruleId)+'.model'
            compiledRule = self.compiler.compileRule(ruleTranslatedPattern,ruleName)
            rule = SRule(compiledRule['lhs'],compiledRule['rhs'],int(maxIterations),self.sendAndApplyDeltaFunc)

        elif self.t['nodes'][ruleId]['$type'] == self.metamodel+"/Query":
            ruleTranslatedPattern = self.createQueryPattern(ruleId)
            ruleName = '/Formalisms/Bird/R_ruleIdNum'+str(ruleId)+'.model'
            compiledRule = self.compiler.compileRule(ruleTranslatedPattern,ruleName)
            rule = Query(compiledRule['lhs'])
        return rule

    
    '''
    finding lhs in a rule
    '''
    def findLhsElements(self,ruleid,element):
        lhsElements = []
        x1= self.t['nodes'][ruleid]['position']['value'][0]
        y1= self.t['nodes'][ruleid]['position']['value'][1]
        x2= self.t['nodes'][ruleid]['position']['value'][0]+273
        y2= self.t['nodes'][ruleid]['position']['value'][1]+250
        for id in element:
            if (x2 >= self.t['nodes'][id]['position']['value'][0]>= x1) and (y2 >= self.t['nodes'][id]['position']['value'][1]>= y1):
                lhsElements.append(id)
        return lhsElements

    '''
    finding rhs in a rule #to work on add edges and return 
    '''
    def findRhsElements(self,ruleid,element):
        rhsElements = []
        x1= self.t['nodes'][ruleid]['position']['value'][0]+274
        y1= self.t['nodes'][ruleid]['position']['value'][1]
        x2= self.t['nodes'][ruleid]['position']['value'][0]+643
        y2= self.t['nodes'][ruleid]['position']['value'][1]+250
        for id in element:
            if x2 >= self.t['nodes'][id]['position']['value'][0]>= x1 and y2 >= self.t['nodes'][id]['position']['value'][1]>= y1:
                rhsElements.append(id)
        return rhsElements

    
    '''
    finding elements in a query
    '''
    def findQueryElements(self,queryid,element):
        queryElements = []
        x1= self.t['nodes'][queryid]['position']['value'][0]
        y1= self.t['nodes'][queryid]['position']['value'][1]
        x2= self.t['nodes'][queryid]['position']['value'][0]+324
        y2= self.t['nodes'][queryid]['position']['value'][1]+250
        for id in element:
            if x2 >= self.t['nodes'][id]['position']['value'][0]>= x1 and y2 >= self.t['nodes'][id]['position']['value'][1]>= y1:
                queryElements.append(id)
        return queryElements
    
    ''' find the starting point to convert lhs, rhs and querry to a pattern
        This is done by finding the empty tile that is not a distnation of another tile in either east or south
        if more than one empty tile found, an error will rise'''
    def findPatternStart(self, idList):
        edges=[]
        for id in idList:
            checkNumOfEdges=[]
            def f(e) :
                return e['dest'] == id
            numEdges = list(filter(f,self.t['edges']))

            for edgeId in numEdges:
                if self.t['nodes'][edgeId['src']]['$type'] == self.birdmodel+"/south" or self.t['nodes'][edgeId['src']]['$type'] == self.birdmodel+"/east":
                    checkNumOfEdges.append(edgeId['src'])
            if self.t['nodes'][id]['$type'] == self.birdmodel+"/Empty" and len(checkNumOfEdges) == 0:
                edges.append(id)
           
        if len(edges) == 1:
            return edges[0]
        else:
            raise RuntimeError('There is a problem with the links in the rule')
    
    
    
    def createRulePattern(self,ruleId):
        label = 0
        labeled=[]
        lhsBirdFacing=''
        rhsBirdFacing=''
        meta="/Formalisms/Bird/Bird.pattern/__p"
        lhs = self.findLhsElements(ruleId,self.ruleBirdNodesId)
        rhs = self.findRhsElements(ruleId,self.ruleBirdNodesId)
        lhsstart= self.findPatternStart(lhs)
        rhsstart= self.findPatternStart(rhs)
        currentLhsNode =   lhsstart
        currentRhsNode =  rhsstart
        self.lastNode = self.lastNode + 1
        lhsNode = self.lastNode
        rule = {'nodes':{}, 'edges':[], 'metamodels':['/Formalisms/__Transformations__/TransformationRule/TransformationRule', '/Formalisms/Bird/Bird.pattern']}
        rule ['nodes'][str(lhsNode)] = {'Condition': {
                                            'type': 'code', 
                                            'value': 'result = True'}, 
                                        '$type': '/Formalisms/__Transformations__/TransformationRule/TransformationRule/LHS'
                                        }
        
        
        self.lastNode = self.lastNode + 1
        rhsNode = self.lastNode
        rule ['nodes'][str(rhsNode)] = {'Action': {
                                            'type': 'code',
                                            'value': 'pass'}, 
                                        '$type': '/Formalisms/__Transformations__/TransformationRule/TransformationRule/RHS'
                                        }
        
        

        def createLhsNode(nodeType):
            rule ['nodes'][str(currentLhsNode)] = {'__pLabel': {
                                                'type': 'string', 
                                                'value': str(label)}, 
                                            '__pPivotIn': {
                                                'type': 'string', 
                                                'value': ''}, 
                                            '__pPivotOut': {
                                                'type': 'string', 
                                                'value': ''}, 
                                            '__pMatchSubtypes': {
                                                'type': 'boolean', 
                                                'value': True}, 
                                            'position': {
                                                'type': 'code', 
                                                'value': 'result = True'}, 
                                            '$type': '/Formalisms/Bird/Bird.pattern/__p'+nodeType}
            labeled.append(currentLhsNode)

        def createRhsNode(nodeType):
            rule ['nodes'][str(currentRhsNode)] = {'__pLabel': {
                                                'type': 'string', 
                                                'value': str(label)}, 
                                            '__pPivotIn': {
                                                'type': 'string', 
                                                'value': ''}, 
                                            '__pPivotOut': {
                                                'type': 'string', 
                                                'value': ''}, 
                                            '__pMatchSubtypes': {
                                                'type': 'boolean'}, 
                                            'position': {
                                                'type': 'code', 
                                                'value': 'result = getAttr()'}, 
                                            '$type': '/Formalisms/Bird/Bird.pattern/__p'+nodeType}
            labeled.append(str(currentRhsNode))

        def createContainmentLinks():
            for link in lhs:
                self.lastNode = self.lastNode + 1
                linkNode = str(self.lastNode)
                rule ['nodes'][linkNode] = {"$type": "/Formalisms/__Transformations__/TransformationRule/TransformationRule/PatternContents"}
                rule['edges'].append({"src": str(lhsNode),"dest":linkNode})
                rule['edges'].append({"src": linkNode,"dest":link})
            for link in rhs:
                self.lastNode = self.lastNode + 1
                linkNode = str(self.lastNode)
                rule ['nodes'][linkNode] = {"$type": "/Formalisms/__Transformations__/TransformationRule/TransformationRule/PatternContents"}
                rule['edges'].append({"src": str(rhsNode),"dest":linkNode})
                rule['edges'].append({"src": linkNode,"dest":link})

        def createOnLink(nodeId,lbl):
            labeled.append(nodeId)
            rule['nodes'][nodeId] = {"__pLabel": {
					                "type": "string",
					                "value": str(lbl)},
				                "__pPivotIn": {
					            "type": "string",
					            "value": ""},
				                "__pPivotOut": {
					            "type": "string",
					            "value": ""},
				                "__pMatchSubtypes": {
					            "type": "boolean",
					            "value": True},
				                "$type": "/Formalisms/Bird/Bird.pattern/__pOn"}
        
        def createLhsTileLink(nodeId,direction):
            labeled.append(nodeId)
            rule['nodes'][nodeId] = {"__pLabel": {
					                "type": "string",
					                "value": str(label)},
				                "__pPivotIn": {
					            "type": "string",
					            "value": ""},
				                "__pPivotOut": {
					            "type": "string",
					            "value": ""},
				                "__pMatchSubtypes": {
					            "type": "boolean",
					            "value": True},
				                "$type": "/Formalisms/Bird/Bird.pattern/__p"+direction}
       
        def createRhsTileLink(nodeId, direction):
            labeled.append(nodeId)
            rule['nodes'][nodeId] = {"__pLabel": {
					                "type": "string",
					                "value": str(label)},
				                "__pPivotIn": {
					            "type": "string",
					            "value": ""},
				                "__pPivotOut": {
					            "type": "string",
					            "value": ""},
				                "__pMatchSubtypes": {
					            "type": "boolean"},
				                "$type": "/Formalisms/Bird/Bird.pattern/__p"+direction}

        def createBirdNode(place,nodeId,f):
            if place == 'lhs':
                f= self.birdMazeFacing= self.t['nodes'][nodeId]['facing']['value']
                labeled.append(nodeId)
                rule['nodes'][nodeId] = {"__pLabel": {
                        					"type": "string",
					                        "value": str(label)},
			                        	"__pPivotIn": {
					                        "type": "string",
					                        "value": ""},
			                        	"__pPivotOut": {
				                        	"type": "string",
					                        "value": ""	},
				                        "__pMatchSubtypes": {
					                        "type": "boolean",
					                        "value": True},
				                        "facing": {
					                        "type": "code",
					                        "value": "result = getAttr()=='"+str(self.birdMazeFacing)+"'"},
				                        "position": {
					                        "type": "code",
					                    "value": "result = getAttr()[0]<"+str(self.MazePosition)},
				                        "$type": "/Formalisms/Bird/Bird.pattern/__pBird"}

            elif place == 'rhs':
                f= self.birdMazeFacing= self.t['nodes'][nodeId]['facing']['value']
                labeled.append(nodeId)
                rule['nodes'][nodeId] = {"__pLabel": {
					                        "type": "string",
					                        "value": str(label)},
				                        "__pPivotIn": {
					                        "type": "string",
				                        	"value": ""},
				                        "__pPivotOut": {
					                        "type": "string",
					                        "value": ""},
				                        "__pMatchSubtypes": {
					                        "type": "boolean"},
				                        "facing": {
					                        "type": "code",
					                        "value": "result ='"+str(f)+"'"},
				                        "position": {
					                        "type": "code",
					                        "value": "result = getAttr()"},
				                        "$type": "/Formalisms/Bird/Bird.pattern/__pBird"}

        def createPigNode(place,nodeId):
            if place == 'lhs':
                labeled.append(nodeId)
                rule['nodes'][nodeId] = {"__pLabel": {
                        					"type": "string",
					                        "value": str(label)},
			                        	"__pPivotIn": {
					                        "type": "string",
					                        "value": ""},
			                        	"__pPivotOut": {
				                        	"type": "string",
					                        "value": ""	},
				                        "__pMatchSubtypes": {
					                        "type": "boolean",
					                        "value": True},
				                        "position": {
					                        "type": "code",
					                    "value": "result = getAttr()[0]<"+str(self.MazePosition)},
				                        "$type": "/Formalisms/Bird/Bird.pattern/__pPig"}

            elif place == 'rhs':
                labeled.append(nodeId)
                rule['nodes'][nodeId] = {"__pLabel": {
					                        "type": "string",
					                        "value": str(label)},
				                        "__pPivotIn": {
					                        "type": "string",
				                        	"value": ""},
				                        "__pPivotOut": {
					                        "type": "string",
					                        "value": ""},
				                        "__pMatchSubtypes": {
					                        "type": "boolean"},
				                        "position": {
					                        "type": "code",
					                        "value": "result = getAttr()"},
				                        "$type": "/Formalisms/Bird/Bird.pattern/__pPig"}

        
        def createEdges(edgeList):
            for xnode in edgeList:
                rule['edges'].append(xnode)
        
        
        def labelBird(lbl):
            for id in lhs:
                if self.checkType(id) == 'Bird':
                    createBirdNode('lhs',id, lhsBirdFacing)
            for id in rhs:
                if self.checkType(id) == 'Bird':
                    createBirdNode('rhs',id, rhsBirdFacing)
            lbl = lbl+1
            return lbl

        def labelPig(lbl):
            for id in lhs:
                if self.checkType(id) == 'Pig':
                    createPigNode('lhs',id)
            for id in rhs:
                if self.checkType(id) == 'Pig':
                    createPigNode('rhs',id)
            lbl = lbl+1
            return lbl

        
        def labelOn(clhs,crhs,lbl):
            currentLhsNode = clhs
            currentRhsNode = crhs
            currentLhsNodeIncommingEdges = self.findFromEdges(currentLhsNode)
            currentRhsNodeIncommingEdges = self.findFromEdges(currentRhsNode)
            for xnode in currentLhsNodeIncommingEdges:
                if xnode['src'] not in labeled:
                    if self.t['nodes'][xnode['src']]['$type']== self.birdmodel+'/On':
                        createOnLink(xnode['src'],lbl)
                        linkedLhsEdges = self.findFromEdges(xnode['src'])
                        linkedLhsNode = linkedLhsEdges[0]['src']
                        for yNode in currentRhsNodeIncommingEdges:
                                if yNode['src'] not in labeled and self.t['nodes'][yNode['src']]['$type']== self.birdmodel+'/On':
                                    linkedRhsEdges = self.findFromEdges(xnode['src'])
                                    linkedRhsNode = linkedRhsEdges[0]['src']
                                    if self.checkType(linkedLhsNode) == self.checkType(linkedRhsNode):
                                        createOnLink(yNode['src'],lbl)
                        lbl = lbl+1
            for yNode in currentRhsNodeIncommingEdges:
                                if yNode['src'] not in labeled and self.t['nodes'][yNode['src']]['$type']== self.birdmodel+'/On':
                                    createOnLink(yNode['src'],lbl)
                                    lbl = lbl+1
            return lbl
        
        label = labelBird(label)
        label = labelPig(label)
        createLhsNode('Empty')
        createRhsNode('Empty')
        label = label +1
        label = labelOn(currentLhsNode,currentRhsNode,label)
        
        #move
        if lhsBirdFacing == rhsBirdFacing:

            
            currentLhsNodeOutgoingEdges = self.findToEdges(currentLhsNode)
            currentRhsNodeOutgoingEdges = self.findToEdges(currentRhsNode)
            for xnode in currentLhsNodeOutgoingEdges:
                currentLhsNode = xnode['dest']
                if currentLhsNode not in labeled:
                    #move south
                    if self.t['nodes'][currentLhsNode]['$type']== self.birdmodel+'/south':
                        createLhsTileLink(currentLhsNode,'south')
                        linkedLhsEdges = self.findToEdges(xnode['dest'])
                        currentLhsNode = linkedLhsEdges[0]['dest']
                        for yNode in currentRhsNodeOutgoingEdges:
                            if yNode['dest'] not in labeled and self.t['nodes'][yNode['dest']]['$type']== self.birdmodel+'/south':
                                createRhsTileLink(yNode['dest'],'south')
                                linkedRhsEdges = self.findToEdges(yNode['dest'])
                                currentRhsNode = linkedRhsEdges[0]['dest']
                        label = label+1
                        createLhsNode('Empty')
                        createRhsNode('Empty')
                        label = label+1
                        label = labelOn(currentLhsNode,currentRhsNode,label)
                    #move east
                    elif self.t['nodes'][currentLhsNode]['$type']== self.birdmodel+'/east':
                        createLhsTileLink(currentLhsNode,'east')
                        linkedLhsEdges = self.findToEdges(xnode['dest'])
                        currentLhsNode = linkedLhsEdges[0]['dest']
                        for yNode in currentRhsNodeOutgoingEdges:
                            if yNode['dest'] not in labeled and self.t['nodes'][yNode['dest']]['$type']== self.birdmodel+'/east':
                                createRhsTileLink(yNode['dest'],'east')
                                linkedRhsEdges = self.findToEdges(yNode['dest'])
                                currentRhsNode = linkedRhsEdges[0]['dest']
                        label = label+1
                        createLhsNode('Empty')
                        createRhsNode('Empty')
                        label = label+1
                        label = labelOn(currentLhsNode,currentRhsNode,label)
        elif lhsBirdFacing != rhsBirdFacing:
            #turn
            currentLhsNodeOutgoingEdges = self.findToEdges(currentLhsNode)
            currentRhsNodeOutgoingEdges = self.findToEdges(currentRhsNode)
            for xnode in currentLhsNodeOutgoingEdges:
                currentLhsNode = xnode['dest']
                if currentLhsNode not in labeled:
                    if self.t['nodes'][currentLhsNode]['$type']== self.birdmodel+'/south':
                        createLhsTileLink(currentLhsNode,'south')
                        linkedLhsEdges = self.findToEdges(xnode['dest'])
                        currentLhsNode = linkedLhsEdges[0]['dest']
                        for yNode in currentRhsNodeOutgoingEdges:
                            if yNode['dest'] not in labeled and self.t['nodes'][yNode['dest']]['$type']== self.birdmodel+'/south':
                                createRhsTileLink(yNode['dest'],'south')
                                linkedRhsEdges = self.findToEdges(yNode['dest'])
                                currentRhsNode = linkedRhsEdges[0]['dest']
                        label = label+1
                        createLhsNode('Empty')
                        createRhsNode('Empty')
                        label = label+1
                        label = labelOn(currentLhsNode,currentRhsNode,label)



        #genertae the edges
        createContainmentLinks()
        for id in lhs:
            currentLhsNodeOutgoingEdges = self.findToEdges(id)
            currentLhsNodeIncommingEdges = self.findFromEdges(id)
            createEdges(currentLhsNodeOutgoingEdges)
            for missingEdge in currentLhsNodeIncommingEdges:
                if missingEdge not in rule['edges']:
                    rule['edges'].append(missingEdge)
        for id in rhs:
            currentRhsNodeOutgoingEdges = self.findToEdges(id)
            currentRhsNodeIncommingEdges = self.findFromEdges(id)
            createEdges(currentRhsNodeOutgoingEdges)
            for missingEdge in currentRhsNodeIncommingEdges:
                if missingEdge not in rule['edges']:
                    rule['edges'].append(missingEdge)
    
        return rule
        
    def createQueryPattern(self,ruleId):
        label = 0
        labeled=[]
        meta="/Formalisms/Bird/Bird.pattern/__p"
        lhs = self.findQueryElements(ruleId,self.ruleBirdNodesId)
        lhsstart= self.findPatternStart(lhs)
        currentLhsNode =   lhsstart
        self.lastNode = self.lastNode + 1
        lhsNode = self.lastNode
        rule = {'nodes':{}, 'edges':[], 'metamodels':['/Formalisms/__Transformations__/TransformationRule/TransformationRule', '/Formalisms/Bird/Bird.pattern']}
        rule ['nodes'][str(lhsNode)] = {'Condition': {
                                            'type': 'code', 
                                            'value': 'result = True'}, 
                                        '$type': '/Formalisms/__Transformations__/TransformationRule/TransformationRule/LHS'
                                        }
        
        
       
        def createLhsNode(nodeType):
            rule ['nodes'][str(currentLhsNode)] = {'__pLabel': {
                                                'type': 'string', 
                                                'value': str(label)}, 
                                            '__pPivotIn': {
                                                'type': 'string', 
                                                'value': ''}, 
                                            '__pPivotOut': {
                                                'type': 'string', 
                                                'value': ''}, 
                                            '__pMatchSubtypes': {
                                                'type': 'boolean', 
                                                'value': True}, 
                                            'position': {
                                                'type': 'code', 
                                                'value': 'result = True'}, 
                                            '$type': '/Formalisms/Bird/Bird.pattern/__p'+nodeType}
            labeled.append(currentLhsNode)

      
        def createContainmentLinks():
            for link in lhs:
                self.lastNode = self.lastNode + 1
                linkNode = str(self.lastNode)
                rule ['nodes'][linkNode] = {"$type": "/Formalisms/__Transformations__/TransformationRule/TransformationRule/PatternContents"}
                rule['edges'].append({"src": str(lhsNode),"dest":linkNode})
                rule['edges'].append({"src": linkNode,"dest":link})

        def createOnLink(nodeId,lbl):
            labeled.append(nodeId)
            rule['nodes'][nodeId] = {"__pLabel": {
					                "type": "string",
					                "value": str(lbl)},
				                "__pPivotIn": {
					            "type": "string",
					            "value": ""},
				                "__pPivotOut": {
					            "type": "string",
					            "value": ""},
				                "__pMatchSubtypes": {
					            "type": "boolean",
					            "value": True},
				                "$type": "/Formalisms/Bird/Bird.pattern/__pOn"}
        
        def createLhsTileLink(nodeId,direction):
            labeled.append(nodeId)
            rule['nodes'][nodeId] = {"__pLabel": {
					                "type": "string",
					                "value": str(label)},
				                "__pPivotIn": {
					            "type": "string",
					            "value": ""},
				                "__pPivotOut": {
					            "type": "string",
					            "value": ""},
				                "__pMatchSubtypes": {
					            "type": "boolean",
					            "value": True},
				                "$type": "/Formalisms/Bird/Bird.pattern/__p"+direction}
       
       
        def createBirdNode(place,nodeId):
            if place == 'lhs':
                labeled.append(nodeId)
                rule['nodes'][nodeId] = {"__pLabel": {
                        					"type": "string",
					                        "value": str(label)},
			                        	"__pPivotIn": {
					                        "type": "string",
					                        "value": ""},
			                        	"__pPivotOut": {
				                        	"type": "string",
					                        "value": ""	},
				                        "__pMatchSubtypes": {
					                        "type": "boolean",
					                        "value": True},
				                        "facing": {
					                        "type": "code",
					                        "value": "result = True"},
				                        "position": {
					                        "type": "code",
					                    "value": "result = getAttr()[0]<"+str(self.MazePosition)},
				                        "$type": "/Formalisms/Bird/Bird.pattern/__pBird"}

            elif place == 'rhs':
                labeled.append(nodeId)
                rule['nodes'][nodeId] = {"__pLabel": {
					                        "type": "string",
					                        "value": str(label)},
				                        "__pPivotIn": {
					                        "type": "string",
				                        	"value": ""},
				                        "__pPivotOut": {
					                        "type": "string",
					                        "value": ""},
				                        "__pMatchSubtypes": {
					                        "type": "boolean"},
				                        "facing": {
					                        "type": "code",
					                        "value": "result = getAttr()"},
				                        "position": {
					                        "type": "code",
					                        "value": "result = getAttr()"},
				                        "$type": "/Formalisms/Bird/Bird.pattern/__pBird"}

        def createPigNode(place,nodeId):
            if place == 'lhs':
                labeled.append(nodeId)
                rule['nodes'][nodeId] = {"__pLabel": {
                        					"type": "string",
					                        "value": str(label)},
			                        	"__pPivotIn": {
					                        "type": "string",
					                        "value": ""},
			                        	"__pPivotOut": {
				                        	"type": "string",
					                        "value": ""	},
				                        "__pMatchSubtypes": {
					                        "type": "boolean",
					                        "value": True},
				                        "position": {
					                        "type": "code",
					                    "value": "result = getAttr()[0]<"+str(self.MazePosition)},
				                        "$type": "/Formalisms/Bird/Bird.pattern/__pPig"}

            elif place == 'rhs':
                labeled.append(nodeId)
                rule['nodes'][nodeId] = {"__pLabel": {
					                        "type": "string",
					                        "value": str(label)},
				                        "__pPivotIn": {
					                        "type": "string",
				                        	"value": ""},
				                        "__pPivotOut": {
					                        "type": "string",
					                        "value": ""},
				                        "__pMatchSubtypes": {
					                        "type": "boolean"},
				                        "position": {
					                        "type": "code",
					                        "value": "result = getAttr()"},
				                        "$type": "/Formalisms/Bird/Bird.pattern/__pPig"}

        
        def createEdges(edgeList):
            for xnode in edgeList:
                rule['edges'].append(xnode)
        
        
        def labelBird(lbl):
            for id in lhs:
                if self.checkType(id) == 'Bird':
                    createBirdNode('lhs',id)
            lbl = lbl+1
            return lbl

        def labelPig(lbl):
            for id in lhs:
                if self.checkType(id) == 'Pig':
                    createPigNode('lhs',id)
           
            lbl = lbl+1
            return lbl

        
        def labelOn(clhs,lbl):
            currentLhsNode = clhs
            currentLhsNodeIncommingEdges = self.findFromEdges(currentLhsNode)
            for xnode in currentLhsNodeIncommingEdges:
                if xnode['src'] not in labeled:
                    if self.t['nodes'][xnode['src']]['$type']== self.birdmodel+'/On':
                        createOnLink(xnode['src'],lbl)
                        linkedLhsEdges = self.findFromEdges(xnode['src'])
                        linkedLhsNode = linkedLhsEdges[0]['src']
                        lbl = lbl+1
            
            return lbl
                                
            
 
        
        label = labelBird(label)
        label = labelPig(label)
        createLhsNode('Empty')
        
        label = label +1
        label = labelOn(currentLhsNode,label)

        #genertae the edges
        createContainmentLinks()
        for id in lhs:
            currentLhsNodeOutgoingEdges = self.findToEdges(id)
            currentLhsNodeIncommingEdges = self.findFromEdges(id)
            createEdges(currentLhsNodeOutgoingEdges)
            for missingEdge in currentLhsNodeIncommingEdges:
                if missingEdge not in rule['edges']:
                    rule['edges'].append(missingEdge)
        
        return rule
        

        
    
    def checkType(self, id):
            if self.t['nodes'][id]['$type'] == self.birdmodel+"/Empty": 
                return 'Empty'
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/Bird":
                return 'Bird'
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/Pig":
                return 'Pig'
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/Tile":
                return 'Tile'
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/On":
                return 'On'
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/east":
                return 'east'
            elif self.t['nodes'][id]['$type'] == self.birdmodel+"/south":
                return 'south'
            


    def findToEdges(self,nodeId):
        def f(e) :
            return e['src'] == nodeId
        return list(filter(f,self.t['edges']))
    
    def findFromEdges(self,nodeId):
        def f(e) :
            return e['dest'] == nodeId
        return list(filter(f,self.t['edges']))


    ''' ptcal integration '''
    
    def setLastStepExecTime(self,a):
        self._lastStep['time'] = a
        self.totalExecutionTime += a

    '''
          returns the id of the current step in the transformation model '''
    def getCurrentStepId(self) :
        if self._lastStep == {} :
            assert False, \
                "this function shouldn't be called when there is no current step"
        else :
            return self._lastStep['id']

    '''
        Returns the initial step of transformation which is the step after start state
    
        Steps to find initial step:
            1- Find start state id in self.t['nodes']
            2- Find the edge where start is the 'src'
            3- The edge has the initial step as 'dest' after the link between
            
        Structure:
            (startID) ----- (linkID) -----> (initialID)
            
            (startID, linkID) is an edge
            (linkID, initialID) is another edge
        
    '''
    def _getInitialStep(self) :

        if self.startStateID==None:
            raise RuntimeError('There is no start state in loaded MoTif instance!')

        startStateEdges = self.findToEdges(self.startStateID)

        initialStepID=None
        if len(startStateEdges) == 0 :
            raise RuntimeError('Start state is not connected to any other state!')
        else:
            firstLinkID=startStateEdges[0]['dest']
            def f(e) :
                return e['src'] == firstLinkID
            startStateEdges = list(filter(f,self.t['edges']))
            initialStepID=startStateEdges[0]['dest']

        if initialStepID in self.rules:
            return self.rules[initialStepID]
        else:
            if self.t['nodes'][initialStepID]['$type']==self.metamodel+"/RuleExit":
                return {'trafoResult':TC.SUCCEEDED,
                        'feedbackReceived':'True'}
            



    '''
        return the next step to run in this transformation... this is either 
        the initial step OR a neighbour of the last step... which one of these
        neighbours is the next step is determined by the application information
        of the said last step 
        
        0. if self._expired is true (i.e., a race condition occurred causing this
            context to be called after it terminated but before ptcal.stop() 
            removed it from ptcal._mtContexts), raise error
        1. if there is no last step, return initial step
        2. filter through edges to find appropriate edge out of last step
            a) if none is found, reset lastStep, set self._expired flag, and 
            return the application information of this entire transformation 
            context
            b) otherwise, return step on the other end of the said edge 
            
        Next step structure
            lastStepID --> successID --> nextID
                   --> failID --> nextID
                   
            
        Steps to find next
            1- Filter edges and get (lastStepID, successID) and (lastStepID,failID) edges
            2- Select success or fail according to _lastStep['applicationInfo']
            3- Find this edge (nextPath, nextStepID) where nextPath is one of the success or fail ids.
            
            
            '''

    def nextStep(self) :
        def getNextStepId(id):
            edgesFromLastStep = self.findToEdges(id)

            if len(edgesFromLastStep) == 0 :
                ai = self._applicationInfo()
                self._lastStep = {}
                self._expired = True
                return ai
            else :

                targetLinkID=None
                resString = None
                LinkID=edgesFromLastStep[0]['dest']
                # make sure it check for success or failer only if the current node is query otherwise it take anytype and pass it
                if self.t['nodes'][edgesFromLastStep[0]['src']]['$type'] == self.metamodel+"/Query":
                    if self._lastStep['applicationInfo'] == TC.SUCCEEDED :
                        resString = self.metamodel+"/success"
                    elif  self._lastStep['applicationInfo'] == TC.FAILED :
                        resString = self.metamodel+"/fail"
                else:
                    resString = self.t['nodes'][LinkID]['$type']
                
                for edgeLS in edgesFromLastStep:
                    if self.t['nodes'][edgeLS['dest']]['$type'] == resString:
                        targetLinkID=edgeLS['dest']
                        break
                        
                nodesAfterLastStep = self.findToEdges(targetLinkID)

                nextStepID = nodesAfterLastStep[0]['dest']
                return nextStepID
        
        # if last step empty retun intial step
        timeNextStep = clock()
        if self._expired == True :
            raise RuntimeError('can not step in expired mtContext')
        elif self._lastStep == {} :
            ns = self._getInitialStep()
            if ns == None :
                return {'$err':'could not find initial transformation step'}
            self._lastStep = ns
            return ns
        else :
            
            edgesFromLastStep = self.findToEdges(self._lastStep['id'])

            if len(edgesFromLastStep) == 0 :
                ai = self._applicationInfo()
                self._lastStep = {}
                self._expired = True
                return ai
            else :
                nextStepID = getNextStepId(self._lastStep['id'])

                if nextStepID in self.rules:
                    self._lastStep = self.rules[nextStepID]
                elif self.t['nodes'][nextStepID]['$type']==self.metamodel+"/RuleEntry":
                    nextStepID = getNextStepId(nextStepID)
                    if nextStepID in self.rules:
                        self._lastStep = self.rules[nextStepID]
                elif self.t['nodes'][nextStepID]['$type']==self.metamodel+"/RuleExit":
                    edgesFromLastStep = self.findToEdges(nextStepID)
                    if len(edgesFromLastStep) == 0 : # end of transformation
                        self._lastStep = {'trafoResult':TC.SUCCEEDED,
                                          'feedbackReceived':'True'}
                    else: # skip the exit and entries in the transformation
                        nextStepID = getNextStepId(nextStepID)
                        nextStepID = getNextStepId(nextStepID)
                        if nextStepID in self.rules:
                            self._lastStep = self.rules[nextStepID]
                else:
                    if self.t['nodes'][nextStepID]['$type']==self.metamodel+"/Entry":
                        self._lastStep = {'trafoResult':TC.SUCCEEDED,
                                          'feedbackReceived':'True'}
                    elif self.t['nodes'][nextStepID]['$type']==self.metamodel+"/exit":
                        self._lastStep = {'trafoResult':TC.SUCCEEDED,
                                          'feedbackReceived':'True'}
                    elif self.t['nodes'][nextStepID]['$type']==self.metamodel+"/next":
                        self._lastStep = {'trafoResult':TC.SUCCEEDED,
                                          'feedbackReceived':'True'}
                    elif self.t['nodes'][nextStepID]['$type']==self.metamodel+"/success":
                        self._lastStep = {'trafoResult':TC.SUCCEEDED,
                                          'feedbackReceived':'True'}
                    elif self.t['nodes'][nextStepID]['$type']==self.metamodel+"/fail":
                        self._lastStep = {'trafoResult':TC.FAILED,
                                          'feedbackReceived':'True'}
                    elif self.t['nodes'][nextStepID]['$type']==self.metamodel+"/SameConnector":
                        self._lastStep = {'trafoResult':TC.SUCCEEDED,
                                          'feedbackReceived':'True'}
 

                return self._lastStep



   
    '''
        set the application information of the last step '''
    def setLastStepApplicationInfo(self,applicationInfo) :
        if applicationInfo == TC.SUCCEEDED :
            self._notApplicable = False
        self._lastStep['applicationInfo'] = applicationInfo


    def isLastStepFeedbackReceived(self) :
        return (not self._expired and self._lastStep=={}) or \
               'feedbackReceived' in self._lastStep
