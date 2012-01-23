'''
Deflectouch

Copyright (C) 2012  Cyril Stoller

For comments, suggestions or other messages, contact me at:
<cyril.stoller@gmail.com>

This file is part of Deflectouch.

Deflectouch is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Deflectouch is distributed in the hope that it will be fun,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Deflectouch.  If not, see <http://www.gnu.org/licenses/>.
'''


import kivy
kivy.require('1.0.9')

from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.image import Image
from kivy.animation import Animation

from kivy.utils import boundary
from math import tan
from math import sin
from math import pi
from math import radians
from kivy.vector import Vector


class Bullet(Image):
    angle = NumericProperty(0) # in radians!
    animation = ObjectProperty(None)
        
    '''
    ####################################
    ##
    ##   Bullet Behavioral
    ##
    ####################################
    '''
    
    def __init__(self, **kwargs):
        super(Bullet, self).__init__(**kwargs)
        
    def fire(self):
        destination = self.calc_destination(self.angle)
        speed = boundary(self.parent.app.config.getint('GamePlay', 'BulletSpeed'), 1, 10)
        self.animation = self.create_animation(speed, destination)
        
        # start the animation
        self.animation.start(self)
        self.animation.bind(on_complete=self.on_collision_with_edge)
        
        # start to track the position changes
        self.bind(pos=self.callback_pos)
        
    
    def create_animation(self, speed, destination):
        # create the animation
        # t = s/v -> v from 1 to 10 / unit-less
        time = Vector(self.center).distance(destination) / (speed * 70)
        return Animation(pos=destination, duration=time)
        
    def calc_destination(self, angle):
        # calculate the path until the bullet hits the edge of the screen
        win = self.get_parent_window()
        left = 130
        right = win.width - 144
        top = win.height - 23
        bottom = 96
        
        bullet_x_to_right = right - self.center_x
        bullet_x_to_left = left - self.center_x
        bullet_y_to_top = top - self.center_y
        bullet_y_to_bottom = bottom - self.center_y
        
        destination_x = 0
        destination_y = 0
        
            
        # this is a little bit ugly, but i couldn't find a nicer way in the hurry
        if 0 <= self.angle < pi/2:
            # 1st quadrant
            if self.angle == 0:
                destination_x = bullet_x_to_right
                destination_y = 0
            else:
                destination_x = boundary(bullet_y_to_top / tan(self.angle), bullet_x_to_left, bullet_x_to_right)
                destination_y = boundary(tan(self.angle) * bullet_x_to_right, bullet_y_to_bottom, bullet_y_to_top)
                
        elif pi/2 <= self.angle < pi:
            # 2nd quadrant
            if self.angle == pi/2:
                destination_x = 0
                destination_y = bullet_y_to_top
            else:
                destination_x = boundary(bullet_y_to_top / tan(self.angle), bullet_x_to_left, bullet_x_to_right)
                destination_y = boundary(tan(self.angle) * bullet_x_to_left, bullet_y_to_bottom, bullet_y_to_top)
                
        elif pi <= self.angle < 3*pi/2:
            # 3rd quadrant
            if self.angle == pi:
                destination_x = bullet_x_to_left
                destination_y = 0
            else:
                destination_x = boundary(bullet_y_to_bottom / tan(self.angle), bullet_x_to_left, bullet_x_to_right)
                destination_y = boundary(tan(self.angle) * bullet_x_to_left, bullet_y_to_bottom, bullet_y_to_top) 
                       
        elif self.angle >= 3*pi/2:
            # 4th quadrant
            if self.angle == 3*pi/2:
                destination_x = 0
                destination_y = bullet_y_to_bottom
            else:
                destination_x = boundary(bullet_y_to_bottom / tan(self.angle), bullet_x_to_left, bullet_x_to_right)
                destination_y = boundary(tan(self.angle) * bullet_x_to_right, bullet_y_to_bottom, bullet_y_to_top)
            
        
        # because all of the calculations above were relative, add the bullet position to it.
        destination_x += self.center_x
        destination_y += self.center_y
        
        return (destination_x, destination_y)
    
    def check_deflector_collision(self, deflector):
        # Here we have a collision Bullet <--> Deflector-bounding-box. But that doesn't mean
        # that there's a collision with the deflector LINE yet. So here's some math stuff
        # for the freaks :) It includes vector calculations, distance problems and trigonometry
        
        # first thing to do is: we need a vector describing the bullet. Length isn't important.
        bullet_position = Vector(self.center)
        bullet_direction = Vector(1, 0).rotate(self.angle * 360 / (2*pi))
        
        # then we need a vector describing the deflector line.
        deflector_vector = Vector(deflector.touch2.pos) - Vector(deflector.touch1.pos)
        
        # now we do a line intersection with the deflector line:
        intersection = Vector.line_intersection(bullet_position, bullet_position + bullet_direction, Vector(deflector.touch1.pos), Vector(deflector.touch2.pos))
        
        # now we want to proof if the bullet comes from the 'right' side.
        # Because it's possible that the bullet is colliding with the deflectors bounding box but
        # would miss / has already missed the deflector line.
        # We do that by checking if the expected intersection point is BEHIND the bullet position.
        # ('behind' means the bullets direction vector points AWAY from the vector 
        # [bullet -> intersection]. That also means the angle between these two vectors is not 0
        # -> due to some math-engine-internal inaccuracies, i have to check if the angle is greater than one:
        if abs(bullet_direction.angle(intersection - bullet_position)) > 1:
            # if the bullet missed the line already - NO COLLISION
            return False
        
        # now we finally check if the bullet is close enough to the deflector line:
        distance = abs(sin(radians(bullet_direction.angle(deflector_vector)) % (pi/2))) * Vector(intersection - bullet_position).length()
        if distance < (self.width / 2):
            # there is a collision!
            '''
            print 'bullet_position: ' , bullet_position
            print 'bullet_direction: ' , bullet_direction
            print 'deflector_vector: ' , deflector_vector
            print 'intersection: ' , intersection
            print 'distance: ' , distance 
            self.animation.stop(self)
            '''
            # kill the animation!
            self.animation.unbind(on_complete=self.on_collision_with_edge)
            self.animation.stop(self)
            # call the collision handler
            self.on_collision_with_deflector(deflector, deflector_vector)
            
        
    
    def callback_pos(self, value, pos):
        # to prevent some strange exception errors:
        if self == None:
            return
        
        # check here if the bullet collides with a deflector, an obstacle or the goal
        # (edge collision detection is irrelevant - the edge is where the bullet animation ends
        # and therefor a callback is raised then)
        
        # first check if there's a collision with deflectors:
        if not len(self.parent.deflector_list) == 0:
            for deflector in self.parent.deflector_list:
                if deflector.collide_widget(self):
                    # if the bullet collides with the bounding box of a deflector
                    # call check_deflector_collision and pass it the colliding instance
                    self.check_deflector_collision(deflector)
        
        # then check if there's a collision with the goal:
        
        
        # then check if there's a collision with obstacles:
        if not len(self.parent.obstacle_list) == 0:
            for obstacle in self.parent.obstacle_list:
                if self.collide_widget(obstacle):
                    self.on_collision_with_obstacle()
    
    def bullet_explode(self):
        self.unbind(pos=self.callback_pos)
        self.animation.unbind(on_complete=self.on_collision_with_edge)
        self.animation.stop(self)
        
        # create an explosion animation
        #bind(animation, self.parent.bullet_died
        self.parent.bullet_died()
        
    def on_collision_with_edge(self, animation, widget):
        print 'edge'
        self.bullet_explode()
    
    def on_collision_with_obstacle(self):
        print 'obstacle'
        self.bullet_explode()
    
    def on_collision_with_deflector(self, deflector, deflector_vector):
        print 'deflector'
        
        # flash up the deflector
        deflector.color = (1, 1, 1)
        Animation(color=(0, 0, 1), duration=1, t='out_expo').start(deflector)
        
        # calculate deflection angle
        impact_angle = (radians(deflector_vector.angle(Vector(1, 0))) % pi) - (self.angle % pi)
        self.angle = (self.angle + 2*impact_angle) % (2*pi)
        
        destination = self.calc_destination(self.angle)
        speed = boundary(self.parent.app.config.getint('GamePlay', 'BulletSpeed'), 1, 10)
        self.animation = self.create_animation(speed, destination)
        
        # start the animation
        self.animation.start(self)
        self.animation.bind(on_complete=self.on_collision_with_edge)
    
    def on_collision_with_goal(self):
        print 'goal'
        self.bullet_explode()
        
        
        
        
        
        
        
        
        
        
        
        