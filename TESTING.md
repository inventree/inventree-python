## Unit Testing

The InvenTree python bindings provide a number of unit tests to ensure the code is working correctly. Tests must be run against an instance of the InvenTree web server.

### Testing Code

Unit testing code is located in the `./test/` directory - test files conform to the filename pattern `test_<xyz>.py`.

### Writing Tests

Any new features should be accompanied by a set of appropriate unit tests, which cover the new features.

## Running Tests

The simplest way to run tests locally is to simply run the following command:

```
invoke test
```

This assumes you have installed, on your path:

- python
- invoke
- docker-compose

The `invoke-test` command performs the following sequence of actions:

- Ensures the test InvenTree server is running (in a docker container)
- Resets the test database to a known state
- Runs the suite of unit tests
