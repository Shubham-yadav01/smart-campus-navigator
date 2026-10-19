"""
Pathfinding and Graph Navigation Module for Smart Campus Navigator.
Implements Dijkstra's algorithm to compute shortest walking routes between campus locations.
"""

import math
import heapq
from typing import Dict, Any, List, Optional, Tuple
from database import get_campus_graph_data


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes the great-circle distance between two GPS coordinates in meters.
    """
    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 1)


def calculate_walking_time(distance_meters: float, walking_speed_mpm: float = 80.0) -> int:
    """
    Calculates estimated walking time in minutes based on distance.
    Standard average campus pedestrian walking speed is ~80 meters/minute (4.8 km/h).
    Returns at least 1 minute if distance > 0.
    """
    if distance_meters <= 0:
        return 0
    mins = round(distance_meters / walking_speed_mpm)
    return max(1, int(mins))


def find_shortest_path(source_id: int, dest_id: int) -> Dict[str, Any]:
    """
    Executes Dijkstra's algorithm on the weighted campus graph to find the shortest
    pedestrian path from source_id to dest_id.

    Returns:
        Dict containing success status, path nodes, distance, walking time, coordinates,
        and step-by-step navigation instructions.
    """
    graph_data = get_campus_graph_data()
    nodes = graph_data["nodes"]
    adjacency = graph_data["adjacency"]

    if source_id not in nodes:
        return {
            "success": False,
            "error": f"Source location (ID {source_id}) does not exist."
        }

    if dest_id not in nodes:
        return {
            "success": False,
            "error": f"Destination location (ID {dest_id}) does not exist."
        }

    source_node = nodes[source_id]
    dest_node = nodes[dest_id]

    # Handle same location
    if source_id == dest_id:
        return {
            "success": True,
            "source": source_node,
            "destination": dest_node,
            "total_distance_meters": 0.0,
            "estimated_time_minutes": 0,
            "path": [source_node],
            "coordinates": [[source_node["latitude"], source_node["longitude"]]],
            "steps": [f"You are already at {source_node['name']}."],
            "turn_by_turn": []
        }

    # Dijkstra's Algorithm
    distances: Dict[int, float] = {node_id: float('inf') for node_id in nodes}
    predecessors: Dict[int, Optional[Tuple[int, str, float]]] = {node_id: None for node_id in nodes}

    distances[source_id] = 0.0
    # Priority Queue stores: (distance, node_id)
    pq: List[Tuple[float, int]] = [(0.0, source_id)]

    while pq:
        curr_dist, u = heapq.heappop(pq)

        if curr_dist > distances[u]:
            continue

        if u == dest_id:
            break

        for edge in adjacency.get(u, []):
            v = edge["to"]
            weight = edge["distance"]
            alt = curr_dist + weight

            if alt < distances[v]:
                distances[v] = alt
                predecessors[v] = (u, edge.get("name", "Campus Walkway"), weight)
                heapq.heappush(pq, (alt, v))

    # Check reachability
    if distances[dest_id] == float('inf'):
        return {
            "success": False,
            "error": f"No pedestrian path found between {source_node['name']} and {dest_node['name']}."
        }

    # Reconstruct Path
    path_ids: List[int] = []
    step_edges: List[Tuple[str, float]] = []
    curr = dest_id

    while curr is not None:
        path_ids.append(curr)
        pred_info = predecessors[curr]
        if pred_info is not None:
            prev_node_id, pathway_name, step_dist = pred_info
            step_edges.append((pathway_name, step_dist))
            curr = prev_node_id
        else:
            curr = None

    path_ids.reverse()
    step_edges.reverse()

    path_nodes = [nodes[nid] for nid in path_ids]
    coordinates = [[node["latitude"], node["longitude"]] for node in path_nodes]
    total_distance = round(distances[dest_id], 1)
    estimated_time = calculate_walking_time(total_distance)

    # Generate Human-Friendly Turn-by-Turn Guidance
    steps: List[str] = []
    turn_by_turn: List[Dict[str, Any]] = []

    steps.append(f"Start at {source_node['name']} ({source_node['code']})")

    for i in range(len(step_edges)):
        pathway_name, step_dist = step_edges[i]
        next_node = path_nodes[i + 1]
        step_text = f"Follow {pathway_name} toward {next_node['name']} ({round(step_dist)} m)"
        steps.append(step_text)
        turn_by_turn.append({
            "from_node": path_nodes[i]["name"],
            "to_node": next_node["name"],
            "pathway": pathway_name,
            "distance_meters": round(step_dist, 1)
        })

    steps.append(f"Arrive at destination: {dest_node['name']} ({dest_node['code']})")

    return {
        "success": True,
        "source": source_node,
        "destination": dest_node,
        "total_distance_meters": total_distance,
        "estimated_time_minutes": estimated_time,
        "node_count": len(path_nodes),
        "path": path_nodes,
        "coordinates": coordinates,
        "steps": steps,
        "turn_by_turn": turn_by_turn
    }
