# Was the BOM Right?

- Package type of my functions are `Zip` (not `Image`).
- Code used to generate the parsed forecasts go into the `bomscraper` code bucket (https://s3.console.aws.amazon.com/s3/buckets/bomscrapercode?region=ap-southeast-2&tab=objects).
- JSON files with parsed forecasts go into the `wasthebomright` bucket (https://s3.console.aws.amazon.com/s3/buckets/wasthebomright?region=ap-southeast-2&tab=objects).
- According to comments on this issue: https://github.com/aws/aws-sam-cli/issues/2419. The CodeUri/build location is different if you've exected `sam build` before doing a `sam deploy`. `sam deploy` seems to create an `ARTIFACTS_DIR` env. variable that is used subsequently. But the manual build step that I have using `bom_scraper_build.sh` seems good enough and circumvents this complexity.

## Development

- Install AWS CLI (https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- Install vscode AWS Toolkit extension
- The AWS SAM CLI supports a project-level configuration file (samconfig.toml) that stores default parameters for its commands. The file's default location is your project's root directory, which contains your project's AWS SAM template file. See https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-config.html.
- Follow the steps below.
- AWS entry point is `app.py`, this contains separate functions for the 3 AWS Lambdas defined in `template.yaml`. The 3 Lambdas have their own modules; `bom_scraper`, `image_generator` and `twitter_bot`.

### 1. Build

Execute `build.sh`. Don't use `sam build`.

### 2. Package

Execute `sam package --template-file template.yaml --output-template-file packaged.yaml --s3-bucket bomscrapercode`

### 3. Deploy

Execute `sam deploy --config-file ./samconfig.toml`. The config file was generated the first time using `sam deploy --guided`, so it can be recreated that again way if required.

## Local execution

The functions can be executed locally (as normal Python scripts) for testing purposes.

```bash
python bom_scraper.py
# creates a file named 'observation_and_forecasts_<todays date>.json' the output/ dir.

python image_generator.py
```

## TODO

- [ ] Create a layer containing my dependencies (beautifulsoup etc.), see https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-upload

## Twitter bot

See https://developer.twitter.com/en/docs/twitter-api/v1.
