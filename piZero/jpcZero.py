import pygame
import sys
import paho.mqtt.client as mqtt

# Constants for window and LED strip
WIDTH = 800
HEIGHT = 100
LED_COUNT = 10  # Number of simulated LEDs
LED_SPACING = WIDTH // LED_COUNT

class FakeLEDStrip:
    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client
        self.led_colors = [(0, 0, 0) for _ in range(LED_COUNT)]
        self.brightness = 255

    def set_led_colors(self, colors):
        self.led_colors = colors
        self.publish_led_state()

    def set_brightness(self, brightness):
        self.brightness = brightness
        self.publish_led_state()

    def publish_led_state(self):
        led_color_str = ",".join([f"{r},{g},{b}" for r, g, b in self.led_colors])
        self.mqtt_client.publish("ledstrip/color", led_color_str)
        self.mqtt_client.publish("ledstrip/brightness", str(self.brightness))

class LEDController:
    def __init__(self, mqtt_client):
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Fake LED Strip Simulation")

        # Initialize fake LED strip
        self.fake_led_strip = FakeLEDStrip(mqtt_client)

    def run(self):
        # Main loop
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear the screen
            self.screen.fill((0, 0, 0))

            # Draw the fake LED strip
            for i, color in enumerate(self.fake_led_strip.led_colors):
                x = i * LED_SPACING
                pygame.draw.circle(self.screen, color, (x + LED_SPACING // 2, HEIGHT // 2), LED_SPACING // 2)

            # Update the display
            pygame.display.flip()

            # Limit the frame rate
            pygame.time.delay(100)

        # Cleanup and exit
        pygame.quit()
        sys.exit()

# MQTT callback when connected to the broker
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with code " + str(rc))
    client.subscribe("ledstrip/color")
    client.subscribe("ledstrip/brightness")

# MQTT callback when a message is received
def on_message(client, userdata, message):
    payload = message.payload.decode()
    if message.topic == "ledstrip/color":
        r, g, b = map(int, payload.split(","))
        led_controller.fake_led_strip.set_led_colors([(r, g, b) for _ in range(LED_COUNT)])
    elif message.topic == "ledstrip/brightness":
        led_controller.fake_led_strip.set_brightness(int(payload))

# Initialize MQTT client
mqtt_client = mqtt.Client("FakeLEDStripClient")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Set MQTT broker address and connect
mqtt_broker = "your_mqtt_broker_address"  # Replace with your broker address
mqtt_client.connect(mqtt_broker, 1883)
mqtt_client.loop_start()

led_controller = LEDController(mqtt_client)
led_controller.run()
