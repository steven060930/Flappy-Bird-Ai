import pygame
from pygame import *
import time
import random
import sys, os
import neat


"""
this is the test project of teaching AI to play the game Flappy Bird
code originated from the old pygame project and had been modified:
https://github.com/steven060930/Flappy-Bird-game/blob/main/main.py 
"""


pygame.init()
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800
FLOOR = 730
FPS = 30
STAT_FONT = pygame.font.SysFont("comicsans", 25)
GAME_OVER_FONT = pygame.font.SysFont("comicsans", 40)
DRAW_LINES = False
GENERATIONS = 30
GEN_NUMBER = 0

bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird3.png")))]
pipe_image = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "pipe.png")))
ground_image = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "base.png")))
background_image = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bg.png")))

class Bird:
    IMGS = bird_images
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.velocity = 0
        self.height = self.y
        self.img_count = 0
        self.image = self.IMGS[0]

    def jump(self):
        self.velocity = -10 
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.velocity *self.tick_count + 1.5 * self.tick_count**2
        # v0 + a t^2

        if d >= 0:
            d = min(16, d)
        else:
            d -= 2

        self.y += d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
    
    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.image = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.image = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.image = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.image = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img= self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2


        # rotate the image based on the center of the screen
        rotated_image = pygame.transform.rotate(self.image, self.tilt)
        new_rectangle = rotated_image.get_rect(center=self.image.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rectangle.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.image)

    
class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0

        # pipe_top is flipped upwards down
        self.PIPE_TOP = pygame.transform.flip(pipe_image, False, True)
        self.PIPE_BOTTOM = pipe_image
        
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        #return if the bird will collide with the pipe (the obstacle)
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)
        top_point = bird_mask.overlap(top_mask, top_offset)

        if bottom_point or top_point:
            return True
        else:
            return False


class Base:
    #keep the base dynamically moving forawrd
    VELOCITY = 5
    WIDTH = ground_image.get_width()
    IMG = ground_image

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        #extending the base (the ground) to the next game window
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen):
    current_highest_score = -1

    win.blit(background_image, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width()-15, 10))

    text = STAT_FONT.render("Gen: " + str(GEN_NUMBER-1), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    text = STAT_FONT.render("Alive: " + str(len(birds)), 1, (255, 255, 255))
    win.blit(text, (10, 50))

    base.draw(win)
    for bird in birds:
        bird.draw(win)

    pygame.display.update()


def main(genomes, config): # eval_genomes
    """
    to boost the efficiency, we run multiple birds within one single generation
    instead of only run one bird each generation
    """
    score = 0
    birds = []
    nets = []
    ge = [] #genomes

    global GEN_NUMBER
    GEN_NUMBER += 1

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        # append all the birds at the same starting position
        g.fitness = 0
        ge.append(g)
        #set the initial fitness value of each bird to be 0


    #base is located at the bottom of the screen
    base = Base(730)
    pipes = [Pipe(700)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    display.set_caption('Flappy Fird Game Project')

    clock = pygame.time.Clock()

    run = True
    while run:
        #set frame per second
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                sys.exit(0)

        #bird.move()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind += 1
        else:
            #create a new generation 
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            # activating the neuron network by input
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
  
            if output[0] > 0.5:
                bird.jump()

        memo = []
        add_pipe = False

        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x) #-> dont processing movements to the bird anymore
                    nets.pop(x)
                    ge.pop(x)
                    #game_over = True
                    #run = False

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                memo.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            # if get through the pipe, we increase the fitness
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in memo:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.image.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
                #pass
                #game_over = True
                #run = False

        base.move()
        draw_window(win, birds, pipes, base, score, GEN_NUMBER)



def run(config_path):
    config = neat.config.Config(
        neat.DefaultGenome, 
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    #create population
    population = neat.Population(config)

    #give input, and visualize the detailed stats

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    #working with fitness function and the number of generations
    # call the main function 30 times
    winner = population.run(main ,GENERATIONS)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "neat-config.txt")
    run(config_path)