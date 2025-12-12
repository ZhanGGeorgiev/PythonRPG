from collections import deque

class PathFinder:
    @staticmethod
    def get_path_bfs(map_obj, start_x, start_y, target_x, target_y, max_dist=20):
        """
        Calculates the shortest path using Breadth-First Search (BFS).
        Returns a list of tuples: [(x, y), (x, y)...]
        """
        if not map_obj.check_cords(target_x, target_y):
            return []

        queue = deque([(start_x, start_y, [])])
        
        visited = set()
        visited.add((start_x, start_y))

        directions = [
            (0, 1),  # Down
            (0, -1), # Up
            (1, 0),  # Right
            (-1, 0)  # Left
        ]

        while queue:
            cx, cy, path = queue.popleft()

            if (cx, cy) == (target_x, target_y):
                return path + [(cx, cy)]

            if len(path) >= max_dist:
                continue

            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy

                if (nx, ny) not in visited:
                    is_target = (nx, ny) == (target_x, target_y)
                    
                    if map_obj.check_cords(nx, ny):
                        if map_obj.is_passable(nx, ny) or is_target:
                            visited.add((nx, ny))
                            new_path = path + [(nx, ny)]
                            queue.append((nx, ny, new_path))
        
        return []

def seek_path(entity, target_x, target_y):
    return PathFinder.get_path_bfs(
        entity.map, 
        entity.x, 
        entity.y, 
        target_x, 
        target_y, 
        entity.vision
    )