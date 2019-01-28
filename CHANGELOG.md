# Changelog

Note that requirements updates are not listed here unless they result in more changes than just updating the version number.

| Date | Summary | Comparison to previous |
|---|---|---|
| 2018-08-29 | Added in additional govuk-frontend macros that were previously ommited (Mostly form related) | [Here](!27) |
| 2018-08-22 | Fixed bugs with unit tests running on Windows machines | [Here](!23) |
| 2018-08-14 | Removed old GOV.UK toolkits and switched to new govuk design system. **🔥 This is a large breaking change** - please read these notes carefully and refer to the attached merge request for details of code changes:<br><ul><li>main.js and main.scss updated to include new initialisation code for GOV components</li><li>Cookie banner code moved into skeleton app since the new kit does not yet define one.</li><li>skeleton layout.html updated significantly to account for new design system.</li><li>jQuery dependency removed since GOV.UK no longer use it. (_Feel free to re-add if your app needs it, but for new applications please favour vanilla JS where feasible._)</li><li>land-registry-elements and govuk-elements-jinja-macros dependencies temporarily removed while these are ported to new kit (To be re-added in a future release). Note: *Any teams already using these would be better to wait for this subsequent release*</li><li>Gulp tasks and package.json tweaked to build new kit</li><li>New GOV.UK documentation can be found here: https://design-system.service.gov.uk/</li></ul>| [Here](!25) |
| 2018-04-18 | Add new environment variable to control how static assets are served in development vs production                | [Here](!22) |
| 2018-04-18 | Updated jQuery to 3.x.                                                                                           | [Here](!21) |
|            | Removed land-registry-gulp-tasks in favour of in-situ gulp tasks (And update to webpack 4, gulp 4)               |             |
|            | *NOTE*: From this point forward IE8 will no longer run JavaScript. Make sure your service is functional without. |             |
| 2018-04-06 | New version of land-registry-gulp-tasks which removes browsersync, disables linting on save, and fixes webpack timing bug | [Here](992f5c227f74d5d6af8367aa97310f957f82170f) |
| 2018-03-06 | Fix `make unittest` command so that it only runs tests in the unit_test folder instead of integration tests as well | [Here](!19) |
| 2018-03-06 | Pass full exception through to application error templates                      | [Here](!19) |
| 2018-03-06 | Small tweak to csrf extension to make it possible to mark views as exempt       | [Here](!19) |
| 2018-03-06 | utils.request_wants_json() moved into utils sub folder                          | [Here](!19) |
| 2018-02-19 | Added Content Security Policy & serve via self signed https cert in dev env     | [Here](!17) |
| 2018-02-08 | Added CSRF protection for Flask-WTForms and rendering of flask flash() messages | [Here](!16) |
| 2018-02-02 | nodejs/gulp frontend build process now back in Dockerfile                                                                      | [Here](!15) |
| 2018-02-02 | Many unit tests added                                                                                                          | [Here](!14) |
| 2018-01-17 | GOV.UK kit now included in the skeleton (Previously had been demoed in gadget-govuk-ui)                                        | [Here](!12) |
|            | Jinja markdown filter now available to generate GOV.UK compatible html from markdown                                           |             |
|            | pip-compile should now be run via ./pipcompilewrapper.sh in order to pick up git dependencies in requirements.txt              |             |
|            | Added flask-wtf as this should be used for processing and validating forms                                                     |             |
|            | Minified CSS/JS now hidden behind a conditional comment to allow us to serve unminified JS to IE8 and avoid IE8 parsing errors |             |
| 2018-01-17 | Allow application errors to be logged at a higher level by passing force_logging=True                              | [Here](!13) |
| 2018-01-15 | Better logging for 404s and other http exceptions so that they report the path                                     | [Here](53c69a6bdd80e1139a0872ba5f659635facff3ca) |  |             |
| 2018-01-12 | Make the app fall over more gracefully if the static assets are missing                                            | [Here](ec499f7dfc827dc902d2ff0396f096c26015d9fc...58e70373d9d6bdbf5d81ce5c9750dd6294c8292f) |  |             |
| 2018-01-09 | Better backwards compatibility for logging                                                                         | [Here](ec499f7dfc827dc902d2ff0396f096c26015d9fc) |  |             |
| 2017-10-06 | Update gulp tasks to v2.0.0. Switched to Webpack and tweaked gulpfile config structure                             | [Here](8e25e6efcc23476c9526c7774de1ba4b3c9db160) |  |             |
| 2017-10-06 | Remove nodejs/gulp build process from Dockerfile                                                                   | [Here](a43006db3ceb40e71a476a6ec18d65ac0ec6c2bd) |
