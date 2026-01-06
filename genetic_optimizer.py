# genetic_optimizer.py
import random
from typing import Tuple, List

class GeneticOptimizer:
    def __init__(
        self,
        simulator,
        fz_range=(1, 12),
        fp1_range=(12, 24),
        fp2_range=(24, 48),
        population_size=20,
        generations=10,
        mutation_rate=0.1,
        crossover_rate=0.8,
        height_weight=0.6,
        width_weight=0.4
    ):
        self.simulator = simulator
        self.FZ_RANGE = fz_range
        self.FP1_RANGE = fp1_range
        self.FP2_RANGE = fp2_range
        self.POPULATION_SIZE = population_size
        self.GENERATIONS = generations
        self.MUTATION_RATE = mutation_rate
        self.CROSSOVER_RATE = crossover_rate
        self.HEIGHT_WEIGHT = height_weight
        self.WIDTH_WEIGHT = width_weight

    def fitness_function(self, fz, fp1, fp2):
        height, width_ps = self.simulator.simulate_eye(fz, fp1, fp2)
        norm_height = height / 1.0      # 假设最大眼高 ~1V
        norm_width = width_ps / 20.0    # 假设最大眼宽 ~20ps
        score = max(0, self.HEIGHT_WEIGHT * norm_height + self.WIDTH_WEIGHT * norm_width)
        return score, height, width_ps

    def initialize_population(self) -> List[Tuple[float, float, float]]:
        population = []
        for _ in range(self.POPULATION_SIZE):
            fz = random.uniform(*self.FZ_RANGE)
            fp1 = random.uniform(*self.FP1_RANGE)
            fp2 = random.uniform(*self.FP2_RANGE)
            population.append((fz, fp1, fp2))
        return population

    def select(self, population):
        fitness_scores = [self.fitness_function(*ind)[0] for ind in population]
        total_score = sum(fitness_scores)
        if total_score == 0:
            return random.choices(population, k=self.POPULATION_SIZE)
        probabilities = [score / total_score for score in fitness_scores]
        return random.choices(population, weights=probabilities, k=self.POPULATION_SIZE)

    def crossover(self, parent1, parent2):
        if random.random() < self.CROSSOVER_RATE:
            cross_point = random.randint(0, 2)
            child1 = list(parent1)
            child2 = list(parent2)
            child1[cross_point:] = parent2[cross_point:]
            child2[cross_point:] = parent1[cross_point:]
            return tuple(child1), tuple(child2)
        else:
            return parent1, parent2

    def mutate(self, individual):
        fz, fp1, fp2 = individual
        if random.random() < self.MUTATION_RATE:
            fz += random.uniform(-0.5, 0.5)
            fz = max(self.FZ_RANGE[0], min(self.FZ_RANGE[1], fz))
        if random.random() < self.MUTATION_RATE:
            fp1 += random.uniform(-1, 1)
            fp1 = max(self.FP1_RANGE[0], min(self.FP1_RANGE[1], fp1))
        if random.random() < self.MUTATION_RATE:
            fp2 += random.uniform(-2, 2)
            fp2 = max(self.FP2_RANGE[0], min(self.FP2_RANGE[1], fp2))
        return (fz, fp1, fp2)

    def optimize(self):
        population = self.initialize_population()
        best_individual = None
        best_score = 0
        best_height = 0
        best_width = 0

        for gen in range(self.GENERATIONS):
            print(f"\n=== 第 {gen + 1} 代 ===")
            gen_scores = []
            for ind in population:
                score, height, width = self.fitness_function(*ind)
                gen_scores.append((score, ind, height, width))
                if score > best_score:
                    best_score = score
                    best_individual = ind
                    best_height = height
                    best_width = width

            gen_scores.sort(reverse=True)
            top_score, top_ind, top_h, top_w = gen_scores[0]
            print(f"当前最优：零点={top_ind[0]:.2f}GHz, 极点1={top_ind[1]:.2f}GHz, 极点2={top_ind[2]:.2f}GHz")
            print(f"眼高={top_h:.4f}V, 眼宽={top_w:.2f}ps, 适应度得分={top_score:.4f}")

            selected = self.select(population)
            next_population = []
            for i in range(0, self.POPULATION_SIZE, 2):
                p1 = selected[i]
                p2 = selected[i + 1] if i + 1 < self.POPULATION_SIZE else selected[0]
                c1, c2 = self.crossover(p1, p2)
                next_population.extend([c1, c2])
            next_population = [self.mutate(ind) for ind in next_population[:self.POPULATION_SIZE]]
            population = next_population

        return best_individual, best_score, best_height, best_width