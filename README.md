# SF Express (HK) Home-Assistant Custom-Component

## IMPORTANT

This integration requires reverse engineering knowledge to obtain the required parameters.

The way to obtain such parameters is not provided.

## Add to HACS

1. Setup `HACS` https://hacs.xyz/docs/setup/prerequisites
2. In `Home Assistant`, click `HACS` on the menu on the left
3. Select `integrations`
4. Click the menu button in the top right hand corner
5. Choose `custom repositories`
6. Enter `https://github.com/thematrixdev/home-assistant-sfexpress` and choose `Integration`, click `ADD`
7. Find and click on `SF-Express HK` in the `custom repositories` list
8. Click the `DOWNLOAD` button in the bottom right hand corner

## Install

1. Go to `Settings`, `Devices and Services`
2. Click the `Add Integration` button
3. Search `SF-Express HK`
4. Go through the configuration flow
5. Restart Home Assistant

## Debug

### Basic

- On Home Assistant, go to `Settigns` -> `Logs`
- Search `SF-Express HK`

### Advanced

- Add these lines to `configuration.yaml`

```yaml
logger:
  default: info
  logs:
    custom_components.sfexpresshk: debug
```

- Restart Home Assistant
- On Home Assistant, go to `Settigns` -> `Logs`
- Search `SF-Express HK`
- Click the `LOAD FULL LOGS` button

## Support

- Open an issue on GitHub
- Specify:
    - What's wrong
    - Home Assistant version
    - SF-Express custom-integration version
    - Logs

## Unofficial support

- Telegram Group https://t.me/smarthomehk

## Tested on

- Ubuntu 24.10
- Home Assistant Container 2025.01
