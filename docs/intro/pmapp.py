# Pymunk application with multiple scenes (spaces)

import pygame
from pygame.locals import *

import pymunk
import pymunk.pygame_util
from pymunk.vec2d import Vec2d
from pymunk.pygame_util import get_mouse_pos, to_pygame, from_pygame

import random, sys, os

# pymunk.pygame_util.positive_y_is_up = True

BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
WHITE = (255, 255, 255)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

space = None

class App:
    """Create a single-window app with multiple spaces (scenes)."""
    spaces = []
    current = None
    size = 640, 240

    def __init__(self):
        """Initialize pygame and the application."""
        pygame.init()
        self.screen = pygame.display.set_mode(App.size)
        self.running = True
        self.stepping = True

        self.rect = Rect((0, 0), App.size)

        # Pymunk physics simulation
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        # self.draw_options.shape_outline_color = RED
        # self.draw_options.shape_dynamic_color = YELLOW
        
        self.dt = 1/50
        self.shortcuts = {
            K_a: 'print(123)',
            K_b: 'Rectangle(pos=get_mouse_pos(self.screen), color=GREEN)',
            K_v: 'Rectangle(pos=get_mouse_pos(self.screen), color=BLUE)',
            
            K_c: 'Circle(pos=get_mouse_pos(self.screen), color=RED)',
            K_n: 'self.next_space()',
            
            K_q: 'self.running = False',
            K_ESCAPE: 'self.running = False',
            K_SPACE: 'self.stepping = not self.stepping',

            K_1: 'self.draw_options.flags ^= 1',
            K_2: 'self.draw_options.flags ^= 2',
            K_3: 'self.draw_options.flags ^= 4',

            K_p: 'self.capture()',
            K_s: 'App.current.space.step(self.dt)',
            K_z: 'App.current.remove_all()',
            K_g: 'App.current.space.gravity = 0, 0',
        }
        
    def run(self):
        """Run the main event loop."""
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                
                elif event.type == KEYDOWN:
                    self.do_shortcut(event)

                elif event.type == MOUSEBUTTONDOWN:
                    self.stepping = False
                    p = from_pygame(event.pos, self.screen)
                    print(p)
                    for shape in App.current.space.shapes:
                        d, info = shape.point_query(p)
                        if d < 0:
                            print(shape)
                            print(shape.__dict__)

                elif event.type == MOUSEMOTION:
                    if event.buttons[0] == 1:
                        self.p1 = from_pygame(event.pos, self.screen)
                    
                elif event.type == MOUSEBUTTONUP:
                    self.stepping = True

            for s in App.current.space.shapes:
                if s.body.position.y < -100:
                    App.current.space.remove(s)

            self.screen.fill(App.current.color)
            
            for obj in App.current.objects:
                obj.draw()
            
            App.current.space.debug_draw(self.draw_options)
            if self.stepping:
                App.current.space.step(self.dt)
            pygame.display.update()

        pygame.quit()

    def do_shortcut(self, event):
        """Find the key/mod combination in the dictionary and execute the cmd."""
        k = event.key
        m = event.mod
        cmd = ''
        if k in self.shortcuts:
            cmd = self.shortcuts[k]
        elif (k, m) in self.shortcuts:
            cmd = self.shortcuts[k, m]
        if cmd != '':
            try:
                exec(cmd)
            except:
                print(f'cmd error: <{cmd}>')

    def next_space(self):
        d = 1
        if pygame.key.get_mods() & KMOD_SHIFT:
            d = -1
        n = len(App.spaces)
        i = App.spaces.index(App.current)
        i = (i+d) % n
        App.current = App.spaces[i]
        pygame.display.set_caption(App.current.caption)

    def draw_positions(self):
        for body in App.current.space.bodies:
            print(body.mass)

    def capture(self):
        """Save a screen capture to the directory of the 
        calling class, under the class name in PNG format."""
        name = type(self).__name__
        module = sys.modules['__main__']
        path, name = os.path.split(module.__file__)
        name, ext = os.path.splitext(name)
        filename = path + '/' + name + '.png'
        pygame.image.save(self.screen, filename)

class Space:
    """Create an independant simulation space with
    - background color
    - caption
    - text objects
    """
    def __init__(self, caption, color=WHITE, gravity=(0, -900)):
        global space

        space = pymunk.Space()
        space.gravity = gravity
        self.space = space
        App.spaces.append(self)
        App.current = self

        self.caption = caption
        self.color = color
        self.objects = []
        pygame.display.set_caption(caption)

    def remove_all(self):
        for s in self.space.shapes:
            self.space.remove(s)

        for b in self.space.bodies:
            self.space.remove(b)

        for c in self.space.constraints:
            self.space.remove(c)

class Obj:
    options = { 'pos': (0, 0),
                'color': None,
                'img': None,
                }

class Circle:
    """Create a circle object in Pymunk."""
    def __init__(self, pos, radius=10, color=None):
        # self.mass = mass
        self.pos = pos
        self.radius = radius
        # self.intertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
    
        # calculate mass and inertia from shape density
        body = pymunk.Body()
        body.position = pos
        shape = pymunk.Circle(body, radius)
        shape.density = 1
        shape.elasticity = 1
        shape.friction = 0.5
        App.current.space.add(body, shape)
        self.body = body

    def kill(self):
        App.current.space.remove(self.body, self.shape)

class Rectangle:
    def __init__(self, pos, size=(20, 20), color=None):
        body = pymunk.Body()
        body.position = pos
        shape = pymunk.Poly.create_box(body, size)
        shape.density = 1
        if color != None:
            shape.color = color

        App.current.space.add(body, shape)
        self.body = body

class Polygon:
    def __init__(self, pos, vertices):
        body = pymunk.Body()
        body.position = pos
        shape = pymunk.Poly(body, vertices)
        shape.friction = 0.5
        shape.collision_type = 1
        shape.density = 1
        App.current.space.add(body, shape)

class Arrow(Polygon):
    def __init__(self, pos):
        vertices = [(-30, 0), (0, 3), (10, 0), (0, -3)]
        super().__init__(pos, vertices)

class Line:
    """Add a static line."""
    def __init__(self, p0, p1):
        body = pymunk.Body(0, 0, pymunk.Body.STATIC)
        seg = pymunk.Segment(body, p0, p1, 2)
        seg.elasticity = 1
        seg.friction = 1
        App.current.space.add(seg)


class Lever:
    """Add a static line."""
    def __init__(self, pos):
        center = pymunk.Body(0, 0, pymunk.Body.STATIC)
        center.position = pos

        limit = pymunk.Body(0, 0, pymunk.Body.STATIC)
        limit.position = pos[0]-100, pos[1]

        body = pymunk.Body(100, 100000)
        body.position = pos
        seg1 = pymunk.Segment(body, (-100, 0), (100, 0), 10)
        seg2 = pymunk.Segment(body, (-100, 0), (-100, 50), 10)

        joint = pymunk.PinJoint(body, center, (0, 0), (0, 0))
        joint2 = pymunk.SlideJoint(body, limit, (-100, 0), (0, 0), 0, 30)

        App.current.space.add(seg1, seg2, body, joint, joint2)

class Box:
    def __init__(self, rect):
        Line(rect.topleft, rect.topright)
        Line(rect.bottomleft, rect.bottomright)
        Line(rect.topleft, rect.bottomleft)
        Line(rect.topright, rect.bottomright)
    
class Car:
    def __init__(self):
        c1 = Circle((100, 100), 30)
        c2 = Circle((300, 100), 30)
        b = Rectangle(pos=(200, 150), size=(100, 60), color=GREEN)


        j0 = pymunk.PinJoint(c1.body, b.body, (0,0), (-50, -30))
        j0.color = RED
        j1 = pymunk.PinJoint(c1.body, b.body, (0,0), (-50, 30))
        j1.color = BLUE
        j2 = pymunk.PinJoint(c2.body, b.body, (0,0), (50, -30))
        j3 = pymunk.PinJoint(c2.body, b.body, (0,0), (50, 30))

        App.current.space.add(j0, j1, j2, j3)

        speed = -1
        App.current.space.add(
            pymunk.SimpleMotor(c1.body, b.body, speed),
            pymunk.SimpleMotor(c2.body, b.body, speed)
        )

class Text:
    font = None
    def __init__(self, text='Text'):
        self.text = text
        self.pos = (20, 20)
        if Text.font == None:
            Text.font = pygame.font.Font(None, 24)
        self.render()
        App.current.objects.append(self)

    def render(self):
        self.img = self.font.render(self.text, True, BLACK)

    def draw(self):
        screen = pygame.display.get_surface()
        screen.blit(self.img, self.pos)

if __name__ == '__main__':
    app = App()

    Space('Cercle', GRAY)
    Line((10, 10), (500, 10))

    Space('Lines', BLACK)
    Line((0, 100), (500, 100))
    Line((200, 300), (600, 400))
    Lever((150, 200))
    Lever((450, 250))

    Space('Pin joint', YELLOW)
    p0 = 100, 100
    p1 = 300, 100
    Circle(p0, 30)
    Circle(p1, 40)
    Line((0, 20), (500, 20))

    Space('Pin joint')
    p0 = 0, 0
    p1 = 640, 0
    p2 = 640, 320
    p3 = 0, 320
    Line(p0, p1)
    Line(p1, p2)
    Line(p2, p3)
    Line(p3, p0)
    c = Circle((100, 100), 30)

    Space('Pin joint')
    Line((0, 0), (600, 0))
    b1 = Circle((100, 100), 30)
    b2 = Circle((300, 100), 60)
    c = pymunk.PinJoint(b1.body, b2.body, (20, 0), (-20, 0))
    App.current.space.add(c)

    Space('Newtons cradle')
    width, height = App.size
    for x in range(-100, 150, 50):
        x += width / 2
        offset_y = height/2
        mass = 10
        radius = 25
        moment = pymunk.moment_for_circle(mass, 0, radius, (0,0))
        body = pymunk.Body(mass, moment)
        body.position = x, -80+offset_y
        body.start_position = Vec2d(body.position)
        shape = pymunk.Circle(body, radius)
        shape.color = (255, 255, 0)
        shape.elasticity = 0.9999999
        App.current.space.add(body, shape)
        pj = pymunk.PinJoint(App.current.space.static_body, body, (x, 80+offset_y), (0,0))
        App.current.space.add(pj)

    Space('Rectanglees')
    Rectangle((100, 100), (40, 60))
    b = Rectangle((300, 200), (40, 60), color=YELLOW)
    print(b.body.shapes)
    # b.body.shapes.color = YELLOW
    Line((0, 0), (600, 0))

    Space('Car')
    Text()
    Box(Rect(app.rect))
    Car()

    Space('Empty space', GRAY)
    Text('Two attached disks')
    Box(Rect(app.rect))
    b = pymunk.Body()
    b.position = 200, 200
    c1 = pymunk.Circle(b, 30)
    c1.density = 1
    c1.elasticity = 0.9
    c2 = pymunk.Circle(b, 50, (50, 0))
    c2.density = 1
    c2.elasticity = 0.9
    App.current.space.add(b, c1, c2)

    p0 = 20, 100
    p1 = 400, 20

    Space('Slope - no friction', WHITE)
    Box(Rect(app.rect))
    s = pymunk.Segment(space.static_body, p0, p1, 5)
    Circle(pos=(100, 200), radius=50)
    space.add(s)

    Space('Slope -friction = 0.5', WHITE)
    Box(Rect(app.rect))
    s = pymunk.Segment(space.static_body, p0, p1, 5)
    s.friction = 0.5
    Circle(pos=(100, 200), radius=50)
    space.add(s)

    Space('Segment and Circle', GRAY)
    Box(Rect(app.rect))
    b = pymunk.Body(1, 1)
    b.position = (100, 100)
    s = pymunk.Segment(b, (-50, 0), (0, 0), 5)
    s1 = pymunk.Segment(b, (0, 70), (0, 0), 5)
    
    s.elasticity = 0.9
    s.friction = 0.5
    space.add(b, s, s1)

    app.run()