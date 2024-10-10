#include <chrono>
#include <csignal>
#include <exception>
#include <memory>
#include <string>
#include <vector>
#include <algorithm>
#include <mutex>

#include "rclcpp/rclcpp.hpp"
#include <random_point_classifier/msg/active_leds.hpp>                    // ActiveLeds message
#include <random_point_classifier/msg/success_detections_two.hpp>         // SuccessDetectionsTwo message

#include <gpiod.h>

#include <cstring>

using namespace std::chrono_literals;

class GpioNorbi : public rclcpp::Node
{
public:
    GpioNorbi()
    : Node("gpio_norbi"), gpio_chip_(nullptr), gpio_line_85_(nullptr), gpio_line_144_(nullptr), current_led_index_(0)
    {
        // Declare parameters with default values
        this->declare_parameter<double>("gpio_delay", 0.2);  // 0.2 seconds delay
        this->declare_parameter<int>("gpio_line_85", 85);    // GPIO line 85
        this->declare_parameter<int>("gpio_line_144", 144);  // GPIO line 144

        // Get parameter values
        this->get_parameter("gpio_delay", gpio_delay_);
        this->get_parameter("gpio_line_85", gpio_line_number_85_);
        this->get_parameter("gpio_line_144", gpio_line_number_144_);

        RCLCPP_INFO(this->get_logger(), "Parameters:");
        RCLCPP_INFO(this->get_logger(), "  gpio_delay: %.2f seconds", gpio_delay_);
        RCLCPP_INFO(this->get_logger(), "  gpio_line_85: %d", gpio_line_number_85_);
        RCLCPP_INFO(this->get_logger(), "  gpio_line_144: %d", gpio_line_number_144_);

        // Initialize GPIO lines
        try {
            gpio_chip_ = gpiod_chip_open("/dev/gpiochip0"); // Open the GPIO chip
            if (!gpio_chip_) {
                RCLCPP_FATAL(this->get_logger(), "Failed to open GPIO chip.");
                throw std::runtime_error("Failed to open GPIO chip.");
            }

            // Initialize GPIO line 85
            gpio_line_85_ = gpiod_chip_get_line(gpio_chip_, gpio_line_number_85_);
            if (!gpio_line_85_) {
                RCLCPP_FATAL(this->get_logger(), "Failed to get GPIO line %d.", gpio_line_number_85_);
                throw std::runtime_error("Failed to get GPIO line 85.");
            }

            if (gpiod_line_request_output(gpio_line_85_, "gpio_norbi", 0) < 0) {
                RCLCPP_FATAL(this->get_logger(), "Failed to request GPIO line %d as output: %s", 
                            gpio_line_number_85_, strerror(errno));
                throw std::runtime_error("Failed to request GPIO line 85 as output.");
            }

            RCLCPP_INFO(this->get_logger(), "GPIO line %d initialized as output.", gpio_line_number_85_);

            // Initialize GPIO line 144
            gpio_line_144_ = gpiod_chip_get_line(gpio_chip_, gpio_line_number_144_);
            if (!gpio_line_144_) {
                RCLCPP_FATAL(this->get_logger(), "Failed to get GPIO line %d.", gpio_line_number_144_);
                throw std::runtime_error("Failed to get GPIO line 144.");
            }

            if (gpiod_line_request_output(gpio_line_144_, "gpio_norbi", 0) < 0) {
                RCLCPP_FATAL(this->get_logger(), "Failed to request GPIO line %d as output: %s", 
                            gpio_line_number_144_, strerror(errno));
                throw std::runtime_error("Failed to request GPIO line 144 as output.");
            }

            RCLCPP_INFO(this->get_logger(), "GPIO line %d initialized as output.", gpio_line_number_144_);
        }
        catch (const std::exception &e) {
            RCLCPP_FATAL(this->get_logger(), "Failed to initialize GPIO: %s", e.what());
            throw; // Rethrow to terminate node initialization
        }

        // Initialize GPIO states to LOW
        setPinStatePersistent(gpio_line_85_, false);
        setPinStatePersistent(gpio_line_144_, false);

        // Initialize previous_active_leds_ as empty
        previous_active_leds_.clear();

        // Initialize current_led_index_
        current_led_index_ = 0;

        // Create a subscription to /active_leds topic
        active_leds_subscription_ = this->create_subscription<random_point_classifier::msg::ActiveLeds>(
            "/active_leds",
            10,
            std::bind(&GpioNorbi::activeLedsCallback, this, std::placeholders::_1)
        );

        // Create a subscription to /success topic
        success_subscription_ = this->create_subscription<random_point_classifier::msg::SuccessDetectionsTwo>(
            "/success",
            10,
            std::bind(&GpioNorbi::successCallback, this, std::placeholders::_1)
        );

        RCLCPP_INFO(this->get_logger(), "gpio_norbi node initialized and subscribed to /active_leds and /success.");
    }

    ~GpioNorbi()
    {
        // Reset GPIO lines to LOW before exiting
        if (gpio_line_85_) {
            gpiod_line_set_value(gpio_line_85_, 0);
            gpiod_line_release(gpio_line_85_);
        }

        if (gpio_line_144_) {
            gpiod_line_set_value(gpio_line_144_, 0);
            gpiod_line_release(gpio_line_144_);
        }

        if (gpio_chip_) {
            gpiod_chip_close(gpio_chip_);
        }

        RCLCPP_INFO(this->get_logger(), "gpio_norbi node shutting down.");
    }

private:
    // Member variables for GPIO
    struct gpiod_chip *gpio_chip_;
    struct gpiod_line *gpio_line_85_;
    struct gpiod_line *gpio_line_144_;
    int gpio_line_number_85_;
    int gpio_line_number_144_;
    double gpio_delay_; // Delay in seconds

    // Subscriptions
    rclcpp::Subscription<random_point_classifier::msg::ActiveLeds>::SharedPtr active_leds_subscription_;
    rclcpp::Subscription<random_point_classifier::msg::SuccessDetectionsTwo>::SharedPtr success_subscription_;

    // Active LEDs list (updated from /active_leds)
    std::vector<int> active_leds_;
    // Previous active LEDs list for comparison
    std::vector<int> previous_active_leds_;

    // Current index in active_leds_
    size_t current_led_index_;

    // Mutex to protect access to active_leds_
    std::mutex leds_mutex_;

    // Timers for GPIO reset
    rclcpp::TimerBase::SharedPtr gpio_reset_timer_85_;
    rclcpp::TimerBase::SharedPtr gpio_reset_timer_144_;

    // Function to handle /active_leds messages
    void activeLedsCallback(const random_point_classifier::msg::ActiveLeds::SharedPtr msg)
    {
        std::lock_guard<std::mutex> lock(leds_mutex_);

        // Check if the incoming active_leds message is different from the previous one
        if (msg->leds == previous_active_leds_) {
            RCLCPP_DEBUG(this->get_logger(), "Received /active_leds message but LEDs have not changed. No update.");
            return;
        }

        // Update active_leds_ and previous_active_leds_
        active_leds_ = msg->leds;
        previous_active_leds_ = msg->leds;

        RCLCPP_INFO(this->get_logger(), "Received /active_leds message with mode: %s and %zu LEDs.", 
                    msg->mode.c_str(), msg->leds.size());

        RCLCPP_INFO(this->get_logger(), "Active LEDs updated:");
        for (const auto &led : active_leds_) {
            RCLCPP_INFO(this->get_logger(), "  %d", led);
        }

        // Reset current_led_index_ since active_leds_ has changed
        current_led_index_ = 0;

        RCLCPP_INFO(this->get_logger(), "Reset current_led_index_ due to active_leds_ update.");
    }

   void successCallback(const random_point_classifier::msg::SuccessDetectionsTwo::SharedPtr msg)
    {
        std::lock_guard<std::mutex> lock(leds_mutex_);

        // Combine led_numbers_right and led_numbers_left into received_leds
        std::vector<int> received_leds = msg->led_numbers_right;
        received_leds.insert(received_leds.end(), msg->led_numbers_left.begin(), msg->led_numbers_left.end());

        RCLCPP_INFO(this->get_logger(), "Received /success message with %zu LEDs.", received_leds.size());

        if (received_leds.empty()) {
            RCLCPP_WARN(this->get_logger(), "Received empty LED list in /success.");
            return;
        }

        // Process each detected LED
        for (const auto &detected_led : received_leds) {
            // Check if all LEDs have been processed
            if (current_led_index_ >= active_leds_.size()) {
                RCLCPP_INFO(this->get_logger(), "All active LEDs have been processed.");
                break;
            }

            // Get the expected LED
            int expected_led = active_leds_[current_led_index_];

            if (detected_led == expected_led) {
                RCLCPP_INFO(this->get_logger(), "Correctly detected expected LED: %d", detected_led);

                // Determine if this is the last LED in active_leds_
                bool is_last = (current_led_index_ == active_leds_.size() - 1);

                if (is_last) {
                    // Handle last LED: Set GPIO 144 high for gpio_delay_ seconds
                    handleLastDetectedLED();
                } else {
                    // Handle intermediate LED: Set GPIO 85 high
                    handleIntermediateDetectedLED(detected_led);
                }

                // Increment current_led_index_
                current_led_index_++;
            } else {
                RCLCPP_WARN(this->get_logger(), "Detected LED %d does not match expected LED %d. Ignoring.", 
                            detected_led, expected_led);
                // Ignore out-of-order detection
            }
        }
    }


    // Function to handle intermediate detected LEDs (set GPIO 85 high)
    void handleIntermediateDetectedLED(int led)
    {
        RCLCPP_INFO(this->get_logger(), "Detected intermediate LED: %d. Setting GPIO %d HIGH.", led, gpio_line_number_85_);
        setPinState(gpio_line_85_, true);

        // Schedule GPIO 85 to set LOW after gpio_delay_
        if (gpio_reset_timer_85_) {
            gpio_reset_timer_85_->cancel();
        }

        gpio_reset_timer_85_ = this->create_wall_timer(
            std::chrono::duration<double>(gpio_delay_),
            [this]() {
                setPinState(gpio_line_85_, false);
                RCLCPP_INFO(this->get_logger(), "Reset GPIO %d to LOW after gpio_delay_.", gpio_line_number_85_);
                gpio_reset_timer_85_->cancel();
            }
        );
    }

    // Function to handle the last detected LED (set GPIO 144 high for gpio_delay_ seconds)
    void handleLastDetectedLED()
    {
        RCLCPP_INFO(this->get_logger(), "Detected last LED in active_leds_. Setting GPIO %d HIGH for %.2f seconds.", 
                    gpio_line_number_144_, gpio_delay_);
        setPinState(gpio_line_144_, true);

        // Schedule GPIO 144 to set LOW after gpio_delay_
        if (gpio_reset_timer_144_) {
            gpio_reset_timer_144_->cancel();
        }

        gpio_reset_timer_144_ = this->create_wall_timer(
            std::chrono::duration<double>(gpio_delay_),
            [this]() {
                setPinState(gpio_line_144_, false);
                RCLCPP_INFO(this->get_logger(), "Reset GPIO %d to LOW after gpio_delay_.", gpio_line_number_144_);
                gpio_reset_timer_144_->cancel();
            }
        );
    }

    // Function to set GPIO state
    void setPinState(struct gpiod_line *line, bool state)
    {
        if (!line) {
            RCLCPP_ERROR(this->get_logger(), "GPIO line not initialized.");
            return;
        }

        if (state) {
            // Set GPIO line to HIGH (1)
            if (gpiod_line_set_value(line, 1) < 0) {
                RCLCPP_ERROR(this->get_logger(), "Failed to set GPIO line to HIGH: %s", strerror(errno));
                return;
            }

            RCLCPP_INFO(this->get_logger(), "Set GPIO line %d to HIGH.", 
                        (line == gpio_line_85_) ? gpio_line_number_85_ : gpio_line_number_144_);
        }
        else {
            // Set GPIO line to LOW
            if (gpiod_line_set_value(line, 0) < 0) {
                RCLCPP_ERROR(this->get_logger(), "Failed to set GPIO line to LOW: %s", strerror(errno));
                return;
            }

            RCLCPP_INFO(this->get_logger(), "Set GPIO line %d to LOW.", 
                        (line == gpio_line_85_) ? gpio_line_number_85_ : gpio_line_number_144_);
        }
    }

    // Function to set GPIO state persistently without Timer
    void setPinStatePersistent(struct gpiod_line *line, bool state)
    {
        setPinState(line, state);
    }
};

int main(int argc, char * argv[])
{
    // Initialize ROS 2
    rclcpp::init(argc, argv);

    // Create the node
    std::shared_ptr<GpioNorbi> node;
    try {
        node = std::make_shared<GpioNorbi>();
    }
    catch (const std::exception &e) {
        RCLCPP_FATAL(rclcpp::get_logger("rclcpp"), "Failed to create gpio_norbi node: %s", e.what());
        return 1;
    }

    // Spin the node
    rclcpp::spin(node);

    // Shutdown ROS 2
    rclcpp::shutdown();
    return 0;
}
