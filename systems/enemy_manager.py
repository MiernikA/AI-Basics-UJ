import random

from entities.enemy import Enemy

CLUSTER_RADIUS = 200
_cluster_counter = 0


def spawn_enemies(num, width, height, obstacles, enemy_radius=12, max_attempts=30):
    enemies = []
    for _ in range(num):
        for attempt in range(max_attempts):
            radius = enemy_radius
            x = random.randint(radius, width - radius)
            y = random.randint(radius, height - radius)

            new_enemy = Enemy(x, y, radius)

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


def trigger_attack_clusters(enemies, min_cluster_size=4, cluster_radius=CLUSTER_RADIUS + 30):
    visited = set()
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
            cid = _next_cluster_id()
            for member in cluster:
                member.state = "attack"
                member.cluster_id = cid
                visited.add(member)
        else:
            visited.update(cluster)
