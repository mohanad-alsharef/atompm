//NOTE: REQUIRES DSL FROM PREVIOUS TEST

let test_utils = require('./test_utils');
let model_building_utils = require('./model_building_utils');

module.exports = {

    beforeEach: function (client, done) {
        client.url('http://localhost:8124/atompm').pause(300).maximizeWindow(done);
    },

    'Login': function (client) {

        test_utils.login(client);
    },

    'Execute Transformation': function (client) {
        model_building_utils.load_model(client, "Formalisms/Pacman", "sample.model");

        model_building_utils.load_transformation(client, "Formalisms/Pacman/OpSem", "T_Pacman_Simulation.model");

        let run_button = "#\\2f Toolbars\\2f TransformationController\\2f TransformationController\\2e buttons\\2e model\\2f play";
        client.click(run_button);

        client.pause(5000);

        let pacman = "html body.default_style div#rootDiv.rootDiv div#contentDiv.contentDiv div#div_container.container div#div_canvas.canvas svg g#/Formalisms/Pacman/Pacman.defaultIcons/PacmanIcon/55.instance.clickable";

        client.waitForElementNotPresent(pacman, 60000, "Pacman killed");

    },

    after: function (client) {
        client.end();
    },


};

