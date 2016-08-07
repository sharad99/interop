/**
 * Controller for the Mission Dashboard page.
 */



/**
 * Controller for the Mission Dashboard page.
 * @param {!angular.Scope} $rootScope The root scope to listen for events.
 * @param {!angular.$routeParams} $routeParams The route parameter service.
 * @param {!Object} Backend The backend service.
 * @final
 * @constructor
 * @struct
 * @ngInject
 */
MissionDashboardCtrl = function($rootScope, $routeParams, Backend) {
    /**
     * @private @const {!angular.$routeParams} The route params service.
     */
    this.routeParams_ = $routeParams;

    /**
     * @private @const {!Object} The backend service.
     */
    this.backend_ = Backend;

    /**
     * @private @const {?Object} The scene built by the map view, via template.
     */
    this.missionScene = null;

    // Whenever the backend data is updated, rebuild the scene.
    $rootScope.$on(
            'Backend.dataUpdated',
            angular.bind(this, this.rebuildMissionScene_));
};


/**
 * Gets the current mission.
 * @return {?Object} The current mission.
 * @export
 */
MissionDashboardCtrl.prototype.getCurrentMission = function() {
    var missionId = this.routeParams_['missionId'];
    if (!missionId || !this.backend_.missions) {
        return null;
    }

    for (var i = 0; i < this.backend_.missions.length; i++) {
        var mission = this.backend_.missions[i];
        if (mission.id == missionId) {
            return mission;
        }
    }

    return null;
};


/**
 * Rebuild the mission scene using the backend data.
 * @private
 */
MissionDashboardCtrl.prototype.rebuildMissionScene_ = function() {
    var telemetry = [];
    if (this.backend_.teams) {
        for (var i = 0; i < this.backend_.teams.length; i++) {
            var team = this.backend_.teams[i];
            if (team.active && this.backend_.telemetry[team.id]) {
                telemetry.push(this.backend_.telemetry[team.id]);
            }
        }
    }

    if (!!this.missionScene) {
        // Rebuild scene with current mission.
        this.missionScene.rebuildScene(
                this.getCurrentMission(), this.backend_.obstacles, telemetry);
    }
};


/**
 * Determines whether a team should be displayed.
 * @param {!Object} team The team to evaluate.
 * @return {!boolean} Whether team should be displayed.
 * @private
 */
MissionDashboardCtrl.prototype.shouldDisplayTeam_ = function(team) {
    return team.on_clock || team.on_timeout || team.active || team.in_air;
};

/**
 * Gets a list of teams which should be displayed.
 * @return {!Array} A list of teams.
 * @export
 */
MissionDashboardCtrl.prototype.getTeamsToDisplay = function() {
    // Check that data has been loaded.
    if (!this.backend_.teams || this.backend_.teams.length == 0) {
        return [];
    }

    // Get all teams which are relevant.
    teams = [];
    for (var i = 0; i < this.backend_.teams.length; i++) {
        if (this.shouldDisplayTeam_(this.backend_.teams[i])) {
            teams.push(this.backend_.teams[i]);
        }
    }
    return teams;
};

/**
 * Gets the telemetry for a team.
 * @param{!Object} team The team for which to get telemetry.
 * @return {?Object} The telemetry for the team.
 * @export
 */
MissionDashboardCtrl.prototype.getTelemetry = function(team) {
    return this.backend_.telemetry[team.id];
};


// Register controller with app.
angular.module('auvsiSuasApp').controller('MissionDashboardCtrl', [
    '$rootScope',
    '$routeParams',
    'Backend',
    MissionDashboardCtrl
]);
