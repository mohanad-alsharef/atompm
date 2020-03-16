/* This file is part of AToMPM - A Tool for Multi-Paradigm Modelling
*  Copyright 2011 by the AToMPM team and licensed under the LGPL
*  See COPYING.lesser and README.md in the root of this project for full details
*/

var __selectionOverlay;
var __highlighted = [];
var __selection;

function __isSelected(it)
{
	return __selection != undefined && utils.contains(__selection['items'],it);
}

/* draw a selection overlay rectangle around the specified (via uri) icons
	1. clear any past __selection
	2. return undefined on undefined argument
	2. extract uri from non-array argument (when select called with event.target)
		... event.target may be:
		a) normal icon: 	selection becomes that icon's uri
		b) center-piece:	selection becomes center-piece and all of its connected
	  							edges
		c) edge:				selection becomes connected center-piece and all of its
								connected edges
	2. remove selected items <edgeTo,centerPiece,edgeFrom> if any of the 3 are
		missing (e.g., when the canvas selection overlay contains only edgeTo or
		centerPiece) 
	3. foreach icon in the updated selection, add its contents if any/applicable
		except when the 'ignoreContents' is set to true
	4. return undefined on empty updated selection
	5. compute a bbox that contains all specified icons/edges
	6. draw a selection overlay rectangle matching computed bbox and style it
		appropriately
	7. remember the drawn rectangle, the computed bbox and the selection in
		__selection 
	8. give rectangle listener to report __EVENT_LEFT_PRESS_SELECTION 
	9. return true (to indicate successfully selecting something) */
function __select(selection,ignoreContents)
{
	if( __selection != undefined )
	{
		__selection['rect'].remove();
		__selection = undefined;
		GeometryUtils.hideGeometryControlsOverlay();
		GeometryUtils.hideTransformationPreviewOverlay();
	}
	if( selection == undefined )
		return;
	else if( ! utils.isArray(selection) )
		/* selection is event.target */
	{
		if( (uri = __vobj2uri(selection)) )
			selection = [uri].concat(
					(__isConnectionType(uri) ? __getConnectedEdges(uri) : []));
		else
			selection = __getConnectionParticipants( __edge2edgeId(selection) );
	}
	else
		/* filter canvas selection for incomplete connection tuples */
	{
		var missingFromSelection = 
				function(required)
				{
					return required.some( 
								function(edgeId) 
									{return ! utils.contains(selection,edgeId);});
				};

		while(
			selection.length > 0 &&
			selection.some(
				function(it)
				{
					if( it in __edges )
						var items 	= __getConnectionParticipants(it);
					else if( __isConnectionType(it) )
						var items = [it].concat(__getConnectedEdges(it));

					if( items != undefined && missingFromSelection(items) )
					{
						utils.filter(selection,items);  
						return true;
					}
				}) ) ;
	}

	/* add icon contents */
	if( !ignoreContents )
	{
		var containedIcons = [];
		selection.forEach(
			function(it)
			{
				if( it in __icons )
					containedIcons = 
						containedIcons.concat( __getIconsInContainer(it) );
			});
		selection = selection.concat( 
							containedIcons.filter(
								function(ci)
								{
									return ! utils.contains(selection,ci);
								}));
	}
	
	/* compute selection bbox */
	if( selection.length == 0 )
		return;
	else if( selection.length == 1 )
		var bbox = __icons[selection[0]]['icon'].getBBox();
	else
		var bbox = __getGlobalBBox(selection);

	__selection = 
		{'items':selection,
		 'bbox':bbox,
		 'rect':__bbox2rect(bbox,'canvas_selection')};
	__selection['rect'].node.onmousedown = 
		function(event)
		{
			if( event.button == 0 )
				BehaviorManager.handleUserEvent(__EVENT_LEFT_PRESS_SELECTION,event);
		};
	__selection['rect'].node.onmouseup = 
		function(event)
		{
			if( event.button == 0 )
				BehaviorManager.handleUserEvent(__EVENT_LEFT_RELEASE_SELECTION,event);
		};
	return true;
}

/* returns true if __selection contains an 'instance' of the given type */
function __selectionContainsType(type)
{
	if( __selection == undefined )
		return false;
	
	return __selection['items'].some(
					function(it)
					{
						return (type == __EDGETYPE && it in __edges) ||
								 (type == __NODETYPE && it in __icons);
		 			});
}


/* temporarily highlight specified icon (e.g., to draw attention on it) without 
 	disrupting other highlighted elements */
function __flash(uri,color,timeout)
{
	__icons[uri]['icon'].highlight({'color':color || 'MediumVioletRed','fill':true});

	function turnOff()
	{
		try			{__icons[uri]['icon'].unhighlight();} 
		catch(err)	{
			console.log(err);
		}
	}
	window.setTimeout(turnOff,timeout || 500);
}

//return EdgesOut items' ID of an icon.
function __getEdgesOutUri(uri)
{
	var edgesOutUriList = [];
	for(i=0;i<__icons[uri]["edgesOut"].length;i++)
	{
		var s = __icons[uri]["edgesOut"][i];
		var t = s.substr(s.indexOf('-')+2,s.length-1);
		edgesOutUriList.push(t);
	}
	return edgesOutUriList;
}

//return edgesOut items' name of an icon, e.g. /startIcon or /RuleIcon
function __getEdgesOutItem(uri)
{
	var edgesOutUriList = [];
	for(i=0;i<__icons[uri]["edgesOut"].length;i++)
	{
		var s = __icons[uri]["edgesOut"][i];
		var t = s.substr(s.indexOf('-')+2,s.length-1);
		var m = t.substr(0,t.indexOf("/",36));
		edgesOutUriList.push(m);
	}
	return edgesOutUriList;
}

//return edgesin items' name of an icon, e.g. /startIcon or /RuleIcon
function __getEdgesInItem(uri)
{
	var edgesInUriList = [];
	for(i=0;i<__icons[uri]["edgesIn"].length;i++)
	{
		var s = __icons[uri]["edgesIn"][i];
		var t = s.substr(0,s.indexOf('-'));
		var m = t.substr(0,t.indexOf("/",36));
		edgesInUriList.push(m);
	}
	return edgesInUriList;
}

function __findStartIcon()
{
	var iconsList=[];
	var starturi="";
	for(item in __icons)
	{
		iconsList.push(item)
	}
	//get the start icon uri
	for(i=0;i<iconsList.length;i++)
	{
		if(iconsList[i].includes("StartIcon"))
		{
			starturi = iconsList[i];
		}
	}
	return starturi;
}

/*
highlight MDE icons and elements in the rule and query icons one by one.
*/
function __highlightOneByOne()
{
	var highlightList=[];
	var starturi = __findStartIcon();
	var next = starturi;
	
	while(next)
	{
		__highlight(next);
		if(next.includes("RuleIcon")|| next.includes("QueryIcon"))
		{
			//elementsInLHS(next);//highlight elements in LHS
			highlightList.push(...elementsInLHS(next));
			//elementsInRHS(next);//high light elements in RHS
			highlightList.push(...elementsInRHS(next));
		}
			
		highlightList.push(...__getEdgesOutUri(next));
		next = highlightList.shift();
	}

	return highlightList;
}

//highlight items of the MDE model and items in the LHS and RHS rules and items matches LHS in the maze.
function __highlightOneByOneWitTimeouts()
{
	var highlightList=[];
	var starturi = __findStartIcon();
	var next = starturi;
	var LHS = [];
	var RHS =[];
	var LHSSingleMatchedList=[];
	var LHSMultipleMatchedList =[];
	
	var step = function() {
		__highlight(next);
		if(next.includes("RuleIcon")|| next.includes("QueryIcon"))
		{
			LHS = elementsInLHS(next);
			LHSSingleMatchedList = __LHSSingleElementMatching(__linearListSorting(LHS));
			LHSMultipleMatchedList = __LHSMultipleElementsMatching(__linearListSorting(RHS));
			RHS = elementsInRHS(next);

			highlightList.push(...LHS);
			if(__linearListSorting(LHS).length === 1)
			{
				highlightList.push(...LHSSingleMatchedList);
			}
			if(__linearListSorting(LHS).length > 1)
			{
				highlightList.push(...LHSMultipleMatchedList);
			}

			highlightList.push(...RHS);//push elements in RHS
		}

		for(k=0;k<__getEdgesOutUri(next).length;k++)//add getEdgesout items that's MDE.
		{
			if(__getEdgesOutUri(next)[k].includes("MDE"))
			{
				highlightList.push(__getEdgesOutUri(next)[k]);
			}
		}
		next = highlightList.shift();
		if(next!=undefined) {
			setTimeout(step,1000);
		}
	
	}

	step();

}

/*
returns a list of icons that's not MDE icon.
*/

//return icons list in the model that's not MDE.
function __findIconsNotMDE()
{
	var iconsList=[];
	for(item in __icons)
	{
		if(!(item.includes("BlockBasedMDE")))
		{
			iconsList.push(item);
		}
	}
	
	return iconsList;
}

//return a list of icons in the maze by specifies the location on the page.
function __findMazeIcons()
{
	var list = __findIconsNotMDE();
	var MazeIconList = [];
	var maxWidth = 500;
	var maxheight = 700;
	for(i=0;i<list.length;i++)
	{
		var x = __icons[list[i]].icon.getBBox().x;
		var y = __icons[list[i]].icon.getBBox().y;
		if(x<maxWidth && y<maxheight)
		{
			//__highlight(list[i]);
			MazeIconList.push(list[i]);
		}
	}
	return MazeIconList;
}


//returns a list of rule icons or query icons ID.
function __findRuleIcon()
{
	var iconsList=[];
	var RuleIconList = [];
	for(item in __icons)
	{
		iconsList.push(item)
	}
	for(i=0;i<iconsList.length;i++)
	{
		if(iconsList[i].includes("RuleIcon")|| iconsList[i].includes("QueryIcon"))
		{
			RuleIconList.push(iconsList[i]);
		}
	}
	return RuleIconList;
}

//returns 
function __findIconsInRule()
{
	debugger;
	var RuleIconList = __findRuleIcon();
	var iconsList = __findIconsNotMDE();
	for(i=0;i<RuleIconList.length;i++)
	{
		var List = [];
		var x = __icons[RuleIconList[i]].icon.getBBox().x;
		var y = __icons[RuleIconList[i]].icon.getBBox().y;
		var maxWidth = __icons[RuleIconList[i]].icon.getBBox().x+__icons[RuleIconList[i]].icon.getBBox().width;
		var maxheight = __icons[RuleIconList[i]].icon.getBBox().y+__icons[RuleIconList[i]].icon.getBBox().height;
		for(j=0;j<iconsList.length;j++)
		{
			if(__icons[iconsList[j]].icon.getBBox().x <= maxWidth && __icons[iconsList[j]].icon.getBBox().x >= x && __icons[iconsList[j]].icon.getBBox().y <= maxheight && __icons[iconsList[j]].icon.getBBox().y >= y)
			{
				__highlight(iconsList[j]);
				List.push(iconsList[j]);
			}
		}
	}
	return List;
}



function __LHSSingleElementMatching(id)
{
	var list=[];
	var MazeIconList = __findMazeIcons();
	for(i=0;i<MazeIconList.length;i++)
	{
		if(MazeIconList[i].includes(id.substr(0,id.indexOf('/',36))))
		{
			list.push(MazeIconList[i]);
		}
	}
	return list;
}

//return the icon type of a entered icon id.
function __IconType(id)
{
	var result = id.substr(0,id.indexOf('/',37));
	result = result.substr(result.indexOf('/',33));
	return result;
}


function __LHSMultipleElementsMatching(list)//ordered list of icon ids
{
	//debugger;
	var finalList =[];
	//var MazeIconList = __findMazeIcons();
	var temp="";
	var currentID = __LHSSingleElementMatching(list[0])[0];
	finalList.push(currentID);
	for(m=0;m<(list.length-1);m++)
	{
		for(n=0;n<__getEdgesOutItem(currentID).length;n++)
		{
			if(__getEdgesOutItem(currentID)[n].includes(__IconType(list[m+1])))
			{
				temp = __getEdgesOutUri(currentID)[n];
				finalList.push(temp);
			}
		}
		currentID = temp;
	}
	return finalList;
}

//sort a list of icons into a root to leaf order
function __linearListSorting(list)
{
	var sortedList = [];
	var currentID="";
	//debugger;
	for(k=0;k<list.length;k++)//find the first item first
	{
		if(__getEdgesInItem(list[k]).length === 0)
		{
			sortedList[0]=list[k];
			currentID = list[k];    
		}
	}
	while(__getEdgesOutUri(currentID).length !==0)
	{
		for(j=0;j<list.length;j++)
		{
			if(__getEdgesOutUri(currentID).includes(list[j]))
			{
				sortedList.push(list[j]);//find the second item
				var temp = list[j];
			}
		}
		currentID = temp;
	}
	return sortedList;
}

//match icons in the rule with the maze, and return a list of matched icons' id.
function __LHSElementsMatching(rule)
{
	debugger;
	var LHSList = elementsInLHS(rule);
	var MazeIconList = __findMazeIcons();
	var MatchedIconsList =[];

	for(i=0;i<LHSList.length;i++)
	{
		if(!(LHSList[i].includes("Link")))
		{
			for(j=0;j<MazeIconList.length;j++)
			{
				if(MazeIconList[j].includes(LHSList[1].substr(0,LHSList[1].length-12)))
				{
					MatchedIconsList.push(...__getEdgesInItem(MazeIconList[j]));
					MatchedIconsList.push(MazeIconList[j]);
					//MatchedIconsList.push(__getEdgesOutUri(MazeIconList[j]));
					__highlight(MazeIconList[j]);
					/*if(__getEdgesOutItem(MatchedIconsList[j]).contains(__getEdgesOutItem(MazeIconList[i])))
					{
						MatchedIconsList.push(MazeIconList[j]);
					}*/
					
			
				}	
			}
		}	
	}
	
	return MatchedIconsList;
}

 
function elementsInLHS(rule)
{
	var list =[];
	var iconsList = __findIconsNotMDE();
	var x =  __icons[rule].icon.getBBox().x;
	var y =  __icons[rule].icon.getBBox().y;
	var maxWidth =  __icons[rule].icon.getBBox().x +__icons[rule].icon.getBBox().width/2;
	var maxheight = __icons[rule].icon.getBBox().y + __icons[rule].icon.getBBox().height;

	for(i=0;i<iconsList.length;i++)
	{
		if(__icons[iconsList[i]].icon.getBBox().x <= maxWidth && __icons[iconsList[i]].icon.getBBox().x >= x && __icons[iconsList[i]].icon.getBBox().y <= maxheight && __icons[iconsList[i]].icon.getBBox().y >= y)
		{
			
			list.push(iconsList[i]);
		}
	}
	return list;
}

function elementsInRHS(rule)
{
	var list =[];
	var iconsList = __findIconsNotMDE();
	var minWidth =  __icons[rule].icon.getBBox().x+__icons[rule].icon.getBBox().width/2;
	var y =  __icons[rule].icon.getBBox().y;
	var maxWidth =  __icons[rule].icon.getBBox().x +__icons[rule].icon.getBBox().width;
	var maxheight = __icons[rule].icon.getBBox().y + __icons[rule].icon.getBBox().height;

	for(i=0;i<iconsList.length;i++)
	{
		if(__icons[iconsList[i]].icon.getBBox().x <= maxWidth && __icons[iconsList[i]].icon.getBBox().x >= minWidth && __icons[iconsList[i]].icon.getBBox().y <= maxheight && __icons[iconsList[i]].icon.getBBox().y >= y)
		{
			
			list.push(iconsList[i]);
		}
	}
	return list;
}


/* if 'uri' isn't already highlighted, unhighlights whatever is (if applicable) 
	and highlights 'uri'... highlighting implies setting 
	
	1. highlighting 'uri'
	2. possibly highlighting 'uri''s cross-formalism neighbors
  	3. possibly setting a timeout to remove the highlight
	4. setting up the __highlighted object like so
		'uri' 	 :: 'uri'
		'turnOff' :: a function that unhighlights 'uri' and nodes from step 2. if 
						 any... the try/catch blocks ensure safety against deletion of
						 highlighted icons */
function __highlight(uri,followCrossFormalismLinks,timeout,color)
{
	if( ! isHighlighted(uri) )
	{
		__unhighlight(uri);

		__icons[uri]['icon'].highlight({'color':color || 'DarkTurquoise','fill':true});

		if( followCrossFormalismLinks != undefined )
		{
			var neighbors = 
				__getCrossFormalismNeighbors(uri,followCrossFormalismLinks);
			neighbors.nodes.forEach(
					function(n)
					{
						if( n != uri )
					  		__icons[n]['icon'].highlight({'color':'Gold','fill':true});
					});
		}

		if( timeout != undefined )
			var tid = window.setTimeout(__unhighlight,timeout);

		__highlighted.push( 
			{'uri':uri,
			 'turnOff':
				 function() 
				 {
					 try			{__icons[uri]['icon'].unhighlight();}
					 catch(err)	{
					 	console.log(err);
					 }

					 if( followCrossFormalismLinks != undefined )
					 	neighbors.nodes.forEach( 
							function(n) {
	  							try			{__icons[n]['icon'].unhighlight();}
								catch(err)	{
	  								console.log(err);
								}
							} );
					 if( timeout != undefined )
						 window.clearTimeout(tid);
				 }});
	}
}


function isHighlighted(uri)
{
	return __highlighted.length > 0 && __highlighted.filter(function(hl) {return uri == hl['uri'];}).length == 1;
}


function __unhighlight(uri)
{
	if( __highlighted.length > 0 )
	{
		__highlighted.filter(function(hl) {return !uri || uri == hl['uri'];}).forEach(function(hl) {hl.turnOff();});
		if (!uri) {
			__highlighted = [];
		} else {
			__highlighted = __highlighted.filter(function(hl) {return uri != hl['uri'];});
		}
		
	}
}

/* return the contents of the selection orverlay rectangle... the max parameter
	is used to stop searching after the specified number of contained icons/edges
	are found */
function __getCanvasSelectionOverlayContents(max)
{
	if( __selectionOverlay == undefined )
		return [];

	var sobbox	 = {'x'		: __selectionOverlay.attr('x'),
						 'y'		: __selectionOverlay.attr('y'),
						 'width' : __selectionOverlay.attr('width'),
						 'height': __selectionOverlay.attr('height')};
		 contents = [];
	[__icons,__edges].some(
			function(A)
			{
				for( var a in A )
				{
					if( A[a]['icon'].isVisible() && 
						 __isBBoxInside(A[a]['icon'].getBBox(),sobbox) )
					{
						contents.push(a);
						if( contents.length == max )
							return true;
					}
				}
			});
	return contents;
}


/* initialize a Raphael.rect originating at (x,y), appropriately styled, and
	that reports events (specifically, mouseup) as if it were the canvas 

	NOTE:: _x0 and _y0 are use to remember the point from where the selection 
			 began */
function __initCanvasSelectionOverlay(x,y)
{
	if( __selectionOverlay != undefined )
		return;

	__selectionOverlay = __canvas.rect(x,y,0,0);
	__selectionOverlay.node.setAttribute('class','canvas_selection_overlay');
	__selectionOverlay.node.setAttribute('_x0',x);
	__selectionOverlay.node.setAttribute('_y0',y);
	__selectionOverlay.node.onmouseup = 
		function(event)
		{
			if( event.button == 0 )
				BehaviorManager.handleUserEvent(__EVENT_LEFT_RELEASE_CANVAS,event);
		};
}


/* returns true if there is at least one icon fully encompassed within the 
 	selection overlay rectangle */
function __isCanvasSelectionOverlayEmpty()
{
	return __getCanvasSelectionOverlayContents(1).length == 0;
}


/* selects contents of and hides canvas selection overlay */
function __selectSelection()
{
	var selectedSomething = __select( __getCanvasSelectionOverlayContents() );
	__selectionOverlay.remove();
	__selectionOverlay = undefined;
	return selectedSomething;
}


/* resizes the selection overlay rectangle following a mouse motion... resizing
	may involve changing x and y attributes because widths and heights can not be
	negative */
function __updateCanvasSelectionOverlay(x,y)
{
	var w = x - parseInt(__selectionOverlay.node.getAttribute('_x0')),
		 h = y - parseInt(__selectionOverlay.node.getAttribute('_y0'));

	if( w < 0 )
	{
		__selectionOverlay.attr('x', x);
		__selectionOverlay.attr('width', -w);
	}
	else
		__selectionOverlay.attr('width', w);

	if( h < 0 )
	{
		__selectionOverlay.attr('y', y);
		__selectionOverlay.attr('height', -h);
	}
	else
		__selectionOverlay.attr('height', h);
}