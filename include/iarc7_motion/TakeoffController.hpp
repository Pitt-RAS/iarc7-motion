////////////////////////////////////////////////////////////////////////////
//
// Takeoff Controller
//
// Handles takeoff
//
////////////////////////////////////////////////////////////////////////////

#ifndef TAKEOFF_CONTROLLER_H
#define TAKEOFF_CONTROLLER_H

#include <ros/ros.h>

#include "actionlib/server/simple_action_server.h"

#include "ros_utils/LinearMsgInterpolator.hpp"
#include "ros_utils/SafeTransformWrapper.hpp"

// ROS message headers
#include "iarc7_motion/GroundInteractionAction.h"
#include "iarc7_msgs/OrientationThrottleStamped.h"

namespace Iarc7Motion
{

typedef actionlib::SimpleActionServer<iarc7_motion::GroundInteractionAction> Server;

enum class TakeoffState { RAMP,
                          ASCEND,
                          DONE };

    class TakeoffController
    {
    public:
        TakeoffController() = delete;

        // Require construction with a node handle and action server
        TakeoffController(ros::NodeHandle& nh, ros::NodeHandle& private_nh, Server& server);

        ~TakeoffController() = default;

        // Don't allow the copy constructor or assignment.
        TakeoffController(const TakeoffController& rhs) = delete;
        TakeoffController& operator=(const TakeoffController& rhs) = delete;

        // Used to reset and check initial conditions for takeoff
        bool __attribute__((warn_unused_result)) resetForTakeover(
            const ros::Time& time);

        // Used to get a uav control message
        bool __attribute__((warn_unused_result)) update(
            const ros::Time& time,
            iarc7_msgs::OrientationThrottleStamped& uav_command);

        /// Waits until this object is ready to begin normal operation
        bool __attribute__((warn_unused_result)) waitUntilReady();

        bool isDone();

        double getHoverThrottle();

    private:
        ros_utils::SafeTransformWrapper transform_wrapper_;

        Server& server_;

        TakeoffState state_;

        // Current throttle setting
        double throttle_;

        // Used to hold the detected hover throttle
        double recorded_hover_throttle_;

        // Max allowed takeoff start height
        const double max_takeoff_start_height_;

        const double takeoff_complete_height_;

        const double takeoff_throttle_ramp_rate_;

        const double takeoff_throttle_bump_;

        // Last time an update was successful
        ros::Time last_update_time_;

        // Max allowed timeout waiting for first velocity and transform
        const ros::Duration startup_timeout_;

        // Max allowed timeout waiting for velocities and transforms
        const ros::Duration update_timeout_;
    };

} // End namespace Iarc7Motion

#endif // TAKEOFF_CONTROLLER_H