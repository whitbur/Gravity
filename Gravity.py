import sys, math, time
import pygame, random
from pygame.locals import *
pygame.init()

# Adjust for a different physics experience.
GRAVITY = 500

# This is a simple sprite that starts at a random location with a random velocity
# and bounces off walls. Looks like a dot, hence the name.
class Dot(pygame.sprite.Sprite):
	def __init__(self, x=-1, y=-1):
		pygame.sprite.Sprite.__init__(self)
		
		# Initialize member variables.
		# I'm using this -1 trick because default arguments are calculated once by python,
		# so all dots would start at the same "random" location. Velocities dx and dy are in pixels/second.
		self.x = x if x!=-1 else random.randint(1,800)
		self.y = y if y!=-1 else random.randint(1,600)
		self.radius = 5
		self.rect = pygame.Rect(self.x-self.radius, self.y-self.radius, 2*self.radius, 2*self.radius)
		self.dx, self.dy = random.random()*600-300, random.random()*600-300
		self.mass = 1
		
	def update(self, screen, dt=17):
		# Move the dot first,
		self.x += self.dx*(dt/1000.0)
		self.y += self.dy*(dt/1000.0)
		
		# Then deal with wall collisions. Lose some speed from inelasticity.
		decay = .5
		if self.x > 800:
			self.x = 799
			self.dx = -decay*abs(self.dx)
		elif self.x < 0:
			self.x = 1
			self.dx = decay*abs(self.dx)
		if self.y > 600:
			self.y = 599
			self.dy = -decay*abs(self.dy)
		elif self.y < 0:
			self.y = 1
			self.dy = decay*abs(self.dy)
		
		# Pygame likes each sprite to have a rect attribute.
		self.rect.width = int(2*self.radius)
		self.rect.center = (int(self.x), int(self.y))
		
		# Finally, draw the dot.
		pygame.draw.circle(screen, (0,0,255), self.rect.center, int(self.radius))
		
# "Splode" is an explosion. It expands from where it is spawned and then kills itself.
class Splode(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		
		# Setup some member variables. Start with a radius of one pixel. Age and duration
		# are measured in milliseconds.
		self.x, self.y = x, y
		self.radius = 1
		self.rect = pygame.Rect(self.x-self.radius, self.y-self.radius, 2*self.radius, 2*self.radius)
		self.age = 0
		self.duration = 500
	
	def update(self, screen, dt=17):
		# Update age and check to see if we've expired.
		self.age += dt
		if self.age >= self.duration:
			self.kill()
			return
		
		# Housekeeping. Pygame likes each sprite to have a rect attribute.
		self.radius = 100*(math.sqrt(float(self.age)/self.duration))
		self.rect.width = int(2*self.radius)
		self.rect.center = (int(self.x), int(self.y))
		
		# Draw the explosion to the screen.
		pygame.draw.circle(screen, (255,0,0), (int(self.x), int(self.y)), int(self.radius))

if __name__ == "__main__":
	screen = pygame.display.set_mode((800,600))
	pygame.display.set_caption("Gravity Simulation")
	clock = pygame.time.Clock()
	last_spawn = time.time()
	
	# Three levels objects, to make sure layers are drawn correctly.
	lvl1 = pygame.sprite.Group() # Background
	lvl2 = pygame.sprite.Group() # Objects
	lvl3 = pygame.sprite.Group() # HUD? Haven't implemented this yet.
	
	# Make some dots to play with
	for i in range(20):
		lvl2.add(Dot())
	
	# Main loop
	while True:
		# Tick the clock. If it's been over .2 seconds since the last frame was drawn, the user
		# has probably dragged the window or paused the simulation somehow. We should treat this
		# gap as one frame, the simulation gets wonky if we don't.
		dt = clock.tick(60)
		dt = 17 if dt > 200 else dt
		
		# Draw the background
		screen.fill((0,0,0))
		
		for event in pygame.event.get():
			if event.type == QUIT:
				# Exit the game if X is clicked
				pygame.quit()
				sys.exit()
			elif event.type == MOUSEBUTTONDOWN and pygame.key.get_pressed()[pygame.K_SPACE]:
				# Space + click makes an explosion
				lvl1.add(Splode(event.pos[0], event.pos[1]))
			elif event.type == MOUSEMOTION and pygame.mouse.get_pressed()[0]:
				# Generate dots by dragging the mouse, no more than 10/second
				if time.time() - last_spawn > .1:
					last_spawn = time.time()
					lvl2.add(Dot(event.pos[0], event.pos[1]))
		
		# Totals for calculating centroid.
		ax = ay = c = 0
		
		# Apply gravity between every object with mass, O(n^2) operation. Expensive!
		stuff = filter(lambda x: hasattr(x, 'mass') and x.mass != 0, lvl2.sprites())
		for thing1 in stuff:
			# Add x and y to total, increment count
			ax += thing1.x
			ay += thing1.y
			c += 1
			for thing2 in stuff:
				if thing1 == thing2:
					# Don't gravitate dots to themselves.
					continue
				else:
					# Calculate distance between objects using Pythagorean Theorem
					dx = thing1.x-thing2.x
					dy = thing1.y-thing2.y
					dist = math.sqrt(dx**2 + dy**2)
					if dist < 1 :
						# Ignore super close objects. Framerate makes this physics wonky.
						continue
					
					# These are the ratios for calculating X and Y axis components of the force.
					px = dx / dist
					py = dy / dist
					
					# This is the formula for gravity. TECHNICALLY gravity should decay quadratically,
					# not linearly as done here. Linear decay looks much better in game, however.
					force = (GRAVITY * thing1.mass * thing2.mass) / dist # **2 for quadratic decay
					
					# Apply force to object's x and y velocity. Brush up on your physics if you think
					# we should be applying this to the x and y position.
					thing1.dx -= px*force
					thing1.dy -= py*force
		
		# Explode stuff!
		explosions = filter(lambda x: isinstance(x, Splode), lvl1.sprites())
		for exp in explosions:
			for dot in filter(lambda x: isinstance(x, Dot), lvl2.sprites()):
				# Calculate distance from center of explosion to center of dot.
				dx = exp.x-dot.x
				dy = exp.y-dot.y
				dist = math.sqrt(dx**2 + dy**2)
				
				# A bit of geometry shows two circles will be intersecting if radius1 + radius2 > distance between.
				# If intersecting, replace the dot with an explosion.
				if dist < exp.radius + dot.radius:
					dot.kill()
					lvl1.add(Splode(int(dot.x), int(dot.y)))
		
		# This draws the centroid to the screen as a green dot. We wouldn't want to draw a centroid
		# when there are no dots on screen; that would cause a divide by zero error.
		if c > 0:
			pygame.draw.circle(screen, (0, 255, 0), (int(ax/c), int(ay/c)), 3)
		
		# Drawing order is important here. This ensures level 2 will be drawn OVER level one, and so on.
		lvl1.update(screen, dt)
		lvl2.update(screen, dt)
		lvl3.update(screen, dt)
		
		# Finally, let pygame update the screen.
		pygame.display.update()