import random

from entities.enemy import Enemy

CLUSTER_RADIUS = 200
_cluster_counter = 0


def spawn_enemies(num, width, height, obstacles, enemy_radius=12, max_attempts=30):
    enemies = []
    center_x, center_y = width // 2, height // 2
    safe_radius = 50

    for _ in range(num):
        for attempt in range(max_attempts):
            radius = enemy_radius
            x = random.randint(radius, width - radius)
            y = random.randint(radius, height - radius)

            new_enemy = Enemy(x, y, radius)

            dist_from_center = ((x - center_x)**2 + (y - center_y)**2) ** 0.5
            if dist_from_center < safe_radius:
                continue

            collision = False
            for ob in obstacles:
                diff = new_enemy.position.sub(ob.collider.position)
                dist = diff.length()
                min_dist = radius + ob.collider.radius
                if dist < min_dist:
                    collision = True
                    break

            if not collision:    
                enemies.append(new_enemy)
                break

    return enemies



def _next_cluster_id():
    global _cluster_counter
    _cluster_counter += 1
    return _cluster_counter


def trigger_attack_clusters(enemies, min_cluster_size=4, cluster_radius=CLUSTER_RADIUS + 30, max_attackers=8):
    visited = set()
    current_attackers = sum(1 for e in enemies if e.state == "attack")

    for e in enemies:
        if e.state == "attack" or e in visited:
            continue

        cluster = [e]
        for other in enemies:
            if other is e or other.state == "attack":
                continue
            if other in visited:
                continue
            if e.position.sub(other.position).length() <= cluster_radius:
                cluster.append(other)

        if len(cluster) >= min_cluster_size:
            remaining_slots = max_attackers - current_attackers
            if remaining_slots <= 0:
                visited.update(cluster)
                continue

            num_to_attack = min(len(cluster), remaining_slots)
            cid = _next_cluster_id()
            for member in cluster[:num_to_attack]:
                member.state = "attack"
                member.cluster_id = cid
                current_attackers += 1
                visited.add(member)

            for member in cluster[num_to_attack:]:
                visited.add(member)
        else:
            visited.update(cluster)

    for e in enemies:
        close_count = 0
        for other in enemies:
            if other is not e:
                if e.position.sub(other.position).length() <= cluster_radius:
                    close_count += 1

        if close_count < 2 and e.state == "attack":
            e.state = "bold" if e.is_bold else "hide"
            e.cluster_id = None


