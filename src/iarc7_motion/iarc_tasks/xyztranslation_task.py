import math
import rospy
import tf2_ros

from geometry_msgs.msg import TwistStamped

from .abstract_task import AbstractTask
from iarc_tasks.task_states import (TaskRunning,
                                    TaskDone,
                                    TaskCanceled,
                                    TaskAborted,
                                    TaskFailed)
from iarc_tasks.task_commands import (VelocityCommand, NopCommand)

from task_utilities.translate_stop_planner import TranslateStopPlanner

class XYZTranslationTaskState(object):
    init = 0
    translate = 1

class XYZTranslationTask(AbstractTask):

    def __init__(self, task_request):
        super(XYZTranslationTask, self).__init__()

        self._canceled = False;

        self._transition = None

        self._x_position = task_request.x_position
        self._y_position = task_request.y_position
        self._z_position = task_request.z_position

        try:
            self._TRANSLATION_XYZ_TOLERANCE = rospy.get_param('~translation_xyz_tolerance')
            self._TRANSFORM_TIMEOUT = rospy.get_param('~transform_timeout')
            self._MIN_MANEUVER_HEIGHT = rospy.get_param('~min_maneuver_height')
        except KeyError as e:
            rospy.logerr('Could not lookup a parameter for xyztranslation task')
            raise

        # Check that we aren't being requested to go below the minimum maneuver height
        # Error straight out if that's the case. If we are currently below the minimum height
        # It will be caught and handled on the next update
        if self._z_position < self._MIN_MANEUVER_HEIGHT :
            raise ValueError('Requested z height was below the minimum maneuver height')

        # fc status?
        self._path_holder = TranslateStopPlanner(self._x_position,
                                                 self._y_position,
                                                 self._z_position)
        self._state = XYZTranslationTaskState.init

    def get_desired_command(self):
        if self._canceled:
            return (TaskCanceled(),)

        if self._state == XYZTranslationTaskState.init:
            self._state = XYZTranslationTaskState.translate

        if self._state == XYZTranslationTaskState.translate:
            try:
                transStamped = self.topic_buffer.get_tf_buffer().lookup_transform(
                        'map',
                        'quad',
                        rospy.Time(0),
                        rospy.Duration(self._TRANSFORM_TIMEOUT))
            except (tf2_ros.LookupException,
                    tf2_ros.ConnectivityException,
                    tf2_ros.ExtrapolationException) as ex:
                rospy.logerr('XYZTranslation Task: Exception when looking up transform')
                rospy.logerr(ex.message)
                return (TaskAborted(msg = 'Exception when looking up transform during xyztranslation'),)
            
            if(transStamped.transform.translation.z > self._MIN_MANEUVER_HEIGHT):
                hold_twist = self._path_holder.get_xyz_hold_response()
                if not self._path_holder.is_done():
                    return (TaskRunning(), VelocityCommand(hold_twist))
                else:
                    return (TaskDone(), VelocityCommand(hold_twist))
            else:
                return (TaskFailed(msg='Fell below minimum manuever height during translation'),)

        return (TaskAborted(msg='Impossible state in takeoff task reached'))

    def cancel(self):
        rospy.loginfo('XYZTranslationTask canceled')
        self._canceled = True
        return True
    
    def set_incoming_transition(self, transition):
        self._transition = transition
