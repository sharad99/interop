"""Tests for the mission_config module."""

import datetime
from auvsi_suas.models import AerialPosition
from auvsi_suas.models import FlyZone
from auvsi_suas.models import GpsPosition
from auvsi_suas.models import MissionConfig
from auvsi_suas.models import UasTelemetry
from auvsi_suas.models import Waypoint
from auvsi_suas.patches.simplekml_patch import Kml
from django.contrib.auth.models import User
from django.test import TestCase


class TestMissionConfigModel(TestCase):
    """Tests the MissionConfig model."""

    def test_unicode(self):
        """Tests the unicode method executes."""
        pos = GpsPosition()
        pos.latitude = 10
        pos.longitude = 100
        pos.save()
        apos = AerialPosition()
        apos.altitude_msl = 1000
        apos.gps_position = pos
        apos.save()
        wpt = Waypoint()
        wpt.position = apos
        wpt.order = 10
        wpt.save()
        config = MissionConfig()
        config.home_pos = pos
        config.emergent_last_known_pos = pos
        config.off_axis_target_pos = pos
        config.sric_pos = pos
        config.air_drop_pos = pos
        config.save()
        config.mission_waypoints.add(wpt)
        config.search_grid_points.add(wpt)
        config.save()
        self.assertTrue(config.__unicode__())

    def create_uas_logs(self, user, entries):
        """Create a list of uas telemetry logs.

        Args:
            user: User to create logs for.
            entries: List of (lat, lon, alt) tuples for each entry.

        Returns:
            List of UasTelemetry objects
        """
        ret = []

        for (lat, lon, alt) in entries:
            pos = GpsPosition()
            pos.latitude = lat
            pos.longitude = lon
            pos.save()
            apos = AerialPosition()
            apos.altitude_msl = alt
            apos.gps_position = pos
            apos.save()
            log = UasTelemetry()
            log.user = user
            log.uas_position = apos
            log.uas_heading = 0
            log.save()
            ret.append(log)

        return ret

    def test_satisfied_waypoints(self):
        """Tests the evaluation of waypoints method."""
        # Create mission config
        gpos = GpsPosition()
        gpos.latitude = 10
        gpos.longitude = 10
        gpos.save()
        config = MissionConfig()
        config.home_pos = gpos
        config.emergent_last_known_pos = gpos
        config.off_axis_target_pos = gpos
        config.sric_pos = gpos
        config.air_drop_pos = gpos
        config.save()

        # Create waypoints for config
        waypoints = [(38, -76, 100), (39, -77, 200), (40, -78, 0)]
        for i, waypoint in enumerate(waypoints):
            (lat, lon, alt) = waypoint
            pos = GpsPosition()
            pos.latitude = lat
            pos.longitude = lon
            pos.save()
            apos = AerialPosition()
            apos.altitude_msl = alt
            apos.gps_position = pos
            apos.save()
            wpt = Waypoint()
            wpt.position = apos
            wpt.order = i
            wpt.save()
            config.mission_waypoints.add(wpt)
        config.save()

        # Create UAS telemetry logs
        user = User.objects.create_user('testuser', 'testemail@x.com',
                                        'testpass')

        def assertSatisfiedWaypoints(expect, got):
            """Assert two satisfied_waypoints return values are equal."""
            self.assertEqual(expect[0], got[0])
            self.assertEqual(expect[1], got[1])
            for k in expect[2].keys():
                self.assertIn(k, got[2])
                self.assertAlmostEqual(expect[2][k], got[2][k], delta=0.1)
            for k in got[2].keys():
                self.assertIn(k, expect[2])

        # Only first is valid.
        entries = [(38, -76, 140), (40, -78, 600), (37, -75, 40)]
        expect = (1, 1, {0: 40, 1: 460785.17})
        logs = self.create_uas_logs(user, entries)
        assertSatisfiedWaypoints(expect, config.satisfied_waypoints(logs))

        # First and last are valid, but missed second, so third doesn't count.
        entries = [(38, -76, 140), (40, -78, 600), (40, -78, 40)]
        expect = (1, 1, {0: 40, 1: 460785.03})
        logs = self.create_uas_logs(user, entries)
        assertSatisfiedWaypoints(expect, config.satisfied_waypoints(logs))

        # Hit all.
        entries = [(38, -76, 140), (39, -77, 180), (40, -78, 40)]
        expect = (3, 3, {0: 40, 1: 20, 2: 40})
        logs = self.create_uas_logs(user, entries)
        assertSatisfiedWaypoints(expect, config.satisfied_waypoints(logs))

        # Hit all, but don't stay within waypoint track.
        entries = [(38, -76, 140), (39, -77, 180), (41, -78, 40),
                   (40, -78, 40)]
        expect = (3, 2, {0: 40, 1: 20, 2: 40})
        logs = self.create_uas_logs(user, entries)
        assertSatisfiedWaypoints(expect, config.satisfied_waypoints(logs))

        # Only hit the first waypoint on run one, hit all on run two.
        entries = [(38, -76, 140),
                   (40, -78, 600),
                   (37, -75, 40),
                   # Run two:
                   (38, -76, 140),
                   (39, -77, 180),
                   (40, -78, 40)]
        expect = (3, 3, {0: 40, 1: 20, 2: 40})
        logs = self.create_uas_logs(user, entries)
        assertSatisfiedWaypoints(expect, config.satisfied_waypoints(logs))

        # Hit all on run one, only hit the first waypoint on run two.
        entries = [(38, -76, 140),
                   (39, -77, 180),
                   (40, -78, 40),
                   # Run two:
                   (38, -76, 140),
                   (40, -78, 600),
                   (37, -75, 40)]
        expect = (3, 3, {0: 40, 1: 20, 2: 40})
        logs = self.create_uas_logs(user, entries)
        assertSatisfiedWaypoints(expect, config.satisfied_waypoints(logs))

        # Remain on the waypoint track only on the second run.
        entries = [(38, -76, 140),
                   (39, -77, 180),
                   (41, -78, 40),
                   (40, -78, 40),
                   # Run two:
                   (38, -76, 140),
                   (39, -77, 180),
                   (40, -78, 40)]
        expect = (3, 3, {0: 40, 1: 20, 2: 40})
        logs = self.create_uas_logs(user, entries)
        assertSatisfiedWaypoints(expect, config.satisfied_waypoints(logs))

        # Keep flying after hitting all waypoints.
        entries = [(38, -76, 140), (39, -77, 180), (40, -78, 40),
                   (30.1, -78.1, 100)]
        expect = (3, 3, {0: 40, 1: 20, 2: 40})
        logs = self.create_uas_logs(user, entries)
        assertSatisfiedWaypoints(expect, config.satisfied_waypoints(logs))

        # Miss last target by a sane distance.
        entries = [(38, -76, 140), (39, -77, 180), (40, -78, 60)]
        expect = (2, 2, {0: 40, 1: 20, 2: 60})
        logs = self.create_uas_logs(user, entries)
        assertSatisfiedWaypoints(expect, config.satisfied_waypoints(logs))


class TestMissionConfigModelSampleMission(TestCase):

    fixtures = ['testdata/sample_mission.json']

    def test_evaluate_teams(self):
        """Tests the evaluation of teams method."""
        user0 = User.objects.get(username='user0')
        user1 = User.objects.get(username='user1')
        config = MissionConfig.objects.get()

        teams = config.evaluate_teams()

        # Contains user0 and user1
        self.assertEqual(2, len(teams))

        # Verify dictionary structure
        for user, val in teams.iteritems():
            self.assertIn('waypoints_satisfied', val)
            self.assertIn('waypoints_satisfied_track', val)

            self.assertIn('mission_clock_time', val)
            self.assertIn('out_of_bounds_time', val)

            self.assertIn('targets', val)
            for target_set in ['manual', 'auto']:
                self.assertIn(target_set, val['targets'])
                keys = ['matched_target_value', 'unmatched_target_count',
                        'targets']
                for key in keys:
                    self.assertIn(key, val['targets'][target_set])
                for t in val['targets'][target_set]['targets'].values():
                    keys = ['match_value', 'image_approved', 'classifications',
                            'location_accuracy', 'actionable']
                    for key in keys:
                        self.assertIn(key, t)

            self.assertIn('uas_telem_times', val)
            self.assertIn('max', val['uas_telem_times'])
            self.assertIn('avg', val['uas_telem_times'])

            self.assertIn('stationary_obst_collision', val)
            self.assertIn(25, val['stationary_obst_collision'])
            self.assertIn(26, val['stationary_obst_collision'])

            self.assertIn('moving_obst_collision', val)
            self.assertIn(25, val['moving_obst_collision'])
            self.assertIn(26, val['moving_obst_collision'])

        # user0 data
        self.assertEqual(1, teams[user0]['waypoints_satisfied'])
        self.assertEqual(1, teams[user0]['waypoints_satisfied_track'])

        self.assertAlmostEqual(2, teams[user0]['mission_clock_time'])
        self.assertAlmostEqual(0.6, teams[user0]['out_of_bounds_time'])

        self.assertAlmostEqual(0.5, teams[user0]['uas_telem_times']['max'])
        self.assertAlmostEqual(1. / 6, teams[user0]['uas_telem_times']['avg'])

        self.assertEqual(
            11, teams[user0]['targets']['manual']['matched_target_value'])
        self.assertEqual(
            1, teams[user0]['targets']['manual']['unmatched_target_count'])
        # Real targets are PKs 1, 2, and 3.
        self.assertEqual(
            'objective',
            teams[user0]['targets']['manual']['targets'][1]['actionable'])
        self.assertEqual(
            None,
            teams[user0]['targets']['manual']['targets'][2]['actionable'])

        self.assertEqual(True, teams[user0]['stationary_obst_collision'][25])
        self.assertEqual(False, teams[user0]['stationary_obst_collision'][26])

        self.assertEqual(True, teams[user0]['moving_obst_collision'][25])
        self.assertEqual(False, teams[user0]['moving_obst_collision'][26])

        # user1 data
        self.assertEqual(2, teams[user1]['waypoints_satisfied'])
        self.assertEqual(1, teams[user0]['waypoints_satisfied_track'])

        self.assertAlmostEqual(18, teams[user1]['mission_clock_time'])
        self.assertAlmostEqual(1.0, teams[user1]['out_of_bounds_time'])

        self.assertAlmostEqual(1.0, teams[user1]['uas_telem_times']['max'])
        self.assertAlmostEqual(2. / 4, teams[user1]['uas_telem_times']['avg'])

        self.assertEqual(False, teams[user1]['stationary_obst_collision'][25])
        self.assertEqual(False, teams[user1]['stationary_obst_collision'][26])

        self.assertEqual(False, teams[user1]['moving_obst_collision'][25])
        self.assertEqual(False, teams[user1]['moving_obst_collision'][26])

    def assert_non_superuser_data(self, data):
        """Tests non-superuser data is correct."""
        self.assertIn('id', data)
        self.assertEqual(3, data['id'])

        self.assertIn('home_pos', data)
        self.assertIn('latitude', data['home_pos'])
        self.assertIn('longitude', data['home_pos'])
        self.assertEqual(38.0, data['home_pos']['latitude'])
        self.assertEqual(-79.0, data['home_pos']['longitude'])

        self.assertIn('fly_zones', data)
        self.assertEqual(1, len(data['fly_zones']))
        self.assertIn('altitude_msl_min', data['fly_zones'][0])
        self.assertEqual(0.0, data['fly_zones'][0]['altitude_msl_min'])
        self.assertIn('altitude_msl_max', data['fly_zones'][0])
        self.assertEqual(20.0, data['fly_zones'][0]['altitude_msl_max'])
        self.assertIn('boundary_pts', data['fly_zones'][0])
        self.assertEqual(4, len(data['fly_zones'][0]['boundary_pts']))
        self.assertIn('latitude', data['fly_zones'][0]['boundary_pts'][0])
        self.assertEqual(37.0,
                         data['fly_zones'][0]['boundary_pts'][0]['latitude'])
        self.assertIn('longitude', data['fly_zones'][0]['boundary_pts'][0])
        self.assertEqual(-75.0,
                         data['fly_zones'][0]['boundary_pts'][0]['longitude'])
        self.assertIn('order', data['fly_zones'][0]['boundary_pts'][0])
        self.assertEqual(0, data['fly_zones'][0]['boundary_pts'][0]['order'])

        self.assertIn('mission_waypoints', data)
        for waypoint in data['mission_waypoints']:
            self.assertIn('id', waypoint)
            self.assertIn('latitude', waypoint)
            self.assertIn('longitude', waypoint)
            self.assertIn('altitude_msl', waypoint)
            self.assertIn('order', waypoint)

        self.assertEqual(2, len(data['mission_waypoints']))

        self.assertEqual(155, data['mission_waypoints'][0]['id'])
        self.assertEqual(38.0, data['mission_waypoints'][0]['latitude'])
        self.assertEqual(-76.0, data['mission_waypoints'][0]['longitude'])
        self.assertEqual(30.0, data['mission_waypoints'][0]['altitude_msl'])
        self.assertEqual(0, data['mission_waypoints'][0]['order'])

        self.assertEqual(156, data['mission_waypoints'][1]['id'])
        self.assertEqual(38.0, data['mission_waypoints'][1]['latitude'])
        self.assertEqual(-77.0, data['mission_waypoints'][1]['longitude'])
        self.assertEqual(60.0, data['mission_waypoints'][1]['altitude_msl'])
        self.assertEqual(1, data['mission_waypoints'][1]['order'])

        self.assertIn('search_grid_points', data)
        for point in data['search_grid_points']:
            self.assertIn('id', point)
            self.assertIn('latitude', point)
            self.assertIn('longitude', point)
            self.assertIn('altitude_msl', point)
            self.assertIn('order', point)

        self.assertEqual(1, len(data['search_grid_points']))

        self.assertEqual(150, data['search_grid_points'][0]['id'])
        self.assertEqual(38.0, data['search_grid_points'][0]['latitude'])
        self.assertEqual(-79.0, data['search_grid_points'][0]['longitude'])
        self.assertEqual(1000.0, data['search_grid_points'][0]['altitude_msl'])
        self.assertEqual(10, data['search_grid_points'][0]['order'])

        self.assertIn('off_axis_target_pos', data)
        self.assertIn('latitude', data['off_axis_target_pos'])
        self.assertIn('longitude', data['off_axis_target_pos'])
        self.assertEqual(38.0, data['off_axis_target_pos']['latitude'])
        self.assertEqual(-79.0, data['off_axis_target_pos']['longitude'])

        self.assertIn('sric_pos', data)
        self.assertIn('latitude', data['sric_pos'])
        self.assertIn('longitude', data['sric_pos'])
        self.assertEqual(38.0, data['sric_pos']['latitude'])
        self.assertEqual(-79.0, data['sric_pos']['longitude'])

        self.assertIn('air_drop_pos', data)
        self.assertIn('latitude', data['air_drop_pos'])
        self.assertIn('longitude', data['air_drop_pos'])
        self.assertEqual(38.0, data['air_drop_pos']['latitude'])
        self.assertEqual(-79.0, data['air_drop_pos']['longitude'])

    def test_non_superuser_json(self):
        """Conversion to dict for JSON."""
        config = MissionConfig.objects.get()
        data = config.json(is_superuser=False)
        self.assert_non_superuser_data(data)

        self.assertNotIn('emergent_last_known_pos', data)
        self.assertNotIn('stationary_obstacles', data)
        self.assertNotIn('moving_obstacles', data)

    def test_superuser_json(self):
        """Conversion to dict for JSON."""
        config = MissionConfig.objects.get()
        data = config.json(is_superuser=True)
        self.assert_non_superuser_data(data)

        self.assertIn('emergent_last_known_pos', data)
        self.assertIn('latitude', data['emergent_last_known_pos'])
        self.assertIn('longitude', data['emergent_last_known_pos'])
        self.assertEqual(38.0, data['emergent_last_known_pos']['latitude'])
        self.assertEqual(-79.0, data['emergent_last_known_pos']['longitude'])

        self.assertIn('stationary_obstacles', data)
        self.assertEqual(2, len(data['stationary_obstacles']))
        for obst in data['stationary_obstacles']:
            self.assertIn('id', obst)
            self.assertIn('latitude', obst)
            self.assertIn('longitude', obst)
            self.assertIn('cylinder_radius', obst)
            self.assertIn('cylinder_height', obst)
        self.assertEqual(25, data['stationary_obstacles'][0]['id'])
        self.assertEqual(10.0,
                         data['stationary_obstacles'][0]['cylinder_height'])
        self.assertEqual(10.0,
                         data['stationary_obstacles'][0]['cylinder_radius'])
        self.assertEqual(38.0, data['stationary_obstacles'][0]['latitude'])
        self.assertEqual(-76.0, data['stationary_obstacles'][0]['longitude'])

        self.assertIn('moving_obstacles', data)
        self.assertEqual(2, len(data['moving_obstacles']))
        for obst in data['moving_obstacles']:
            self.assertIn('id', obst)
            self.assertIn('speed_avg', obst)
            self.assertIn('sphere_radius', obst)
        self.assertEqual(25, data['moving_obstacles'][0]['id'])
        self.assertEqual(1.0, data['moving_obstacles'][0]['speed_avg'])
        self.assertEqual(15.0, data['moving_obstacles'][0]['sphere_radius'])

    def test_toKML(self):
        """Test Generation of kml for all mission data"""
        kml = Kml()
        MissionConfig.kml_all(kml=kml)
        data = kml.kml()
        names = [
            'Off Axis',
            'SRIC',
            'Home Position',
            'Air Drop',
            'Emergent LKP',
            'Search Area',
            'Waypoints',
        ]
        for name in names:
            tag = '<name>{}</name>'.format(name)
            err = 'tag "{}" not found in {}'.format(tag, data)
            self.assertIn(tag, data, err)
