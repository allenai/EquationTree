from geosolver.diagram.computational_geometry import distance_between_points, midpoint, cartesian_angle, \
    signed_distance_between_cartesian_angles, arc_midpoint, line_length, arc_length
from geosolver.ontology.instantiator_definitions import instantiators
import numpy as np

__author__ = 'minjoon'


def label_distance_to_line(label_point, line, is_length):
    """
    minimum distance among:
    end points, mid point.

    :param point:
    :param line:
    :return:
    """
    mp = midpoint(line.a, line.b)
    distance = distance_between_points(label_point, mp)
    if is_length:
        return distance

    l = 1.0/line_length(line)  # To favor longer line if matching near the points
    return min(distance,
               distance_between_points(label_point, line.a) + l,
               distance_between_points(label_point, line.b) + l)


def label_distance_to_arc(label_point, arc):
    return distance_between_points(label_point, arc_midpoint(arc))


def label_distance_to_angle(label_point, angle):
    """
    If outside of the convex area, then distance is very high.
    :param point:
    :param angle:
    :return:
    """
    caa = cartesian_angle(angle.b, angle.a)
    cam = cartesian_angle(angle.b, label_point)
    cac = cartesian_angle(angle.b, angle.c)
    dm = signed_distance_between_cartesian_angles(cam, caa)
    dc = signed_distance_between_cartesian_angles(cac, caa)
    cav = caa + dc/2.0
    if cav > 2*np.pi:
        cav -= 2*np.pi
    cad = min(signed_distance_between_cartesian_angles(cam, cav), signed_distance_between_cartesian_angles(cav, cam))
    dist = distance_between_points(label_point, angle.b)
    if dc > dm:
        return dist*(1+cad+dc)
    else:
        return 100*dist  # effectively infinite


def label_distance_to_point(label_point, point):
    return distance_between_points(label_point, point)