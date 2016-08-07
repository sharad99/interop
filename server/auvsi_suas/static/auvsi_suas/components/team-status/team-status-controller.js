/**
 * @fileoverview Directive for team status view.
 */


/**
 * Directive for the team status view.
 * @final
 * @constructor
 * @struct
 * @ngInject
 */
TeamStatusCtrl = function() {
    /**
     * @export {?Object} The team object, injected by directive.
     */
    this.team;

    /**
     * @export {?Object} The telemetry object, injected by directive.
     */
    this.telemetry;
};

/**
 * Gets the classes used to color a team's display on the dashboard.
 * @return {!string} The color classes.
 * @export
 */
TeamStatusCtrl.prototype.getTeamColorClasses = function() {
    classes = [];
    if (this.team.active) {
        classes.push('team-status-active');
    }
    if (this.team.in_air) {
        classes.push('team-status-in-air');
    }
    return classes.join(' ');
};

// Register the directive.
angular.module('auvsiSuasApp').directive('teamStatus', [
    function() {
        return {
            restrict: 'E',
            scope: {},
            bindToController: {
                team: '=',
                telemetry: '='
            },
            controller: TeamStatusCtrl,
            controllerAs: 'teamStatusCtrl',
            templateUrl: ('/static/auvsi_suas/components/' +
                          'team-status/team-status.html'),
        };
    }
]);
