---
title: Installation
nav_order: 2
---

# Installation

## Before you start

Media Center must be running, reachable from Home Assistant, and have the Media Network
service enabled.

### Enable Media Network in Media Center

1. Open **Options > Media Network**.
2. Tick **"Use Media Network to share this library and enable DLNA"**.
3. Note the **port**. It is `52199` by default.
4. Note the **access key** shown on the same page. It is a short alphanumeric string such as
   `AbCdEf`. Using it lets the integration find the server again after the machine changes IP
   address.
5. If you want the server to require a login, open **Options > Media Network >
   Authentication** and set a user name and password. The integration asks for them during
   setup.

Nothing else needs configuring on the Media Center side. The integration never writes to
Media Center's own configuration.

## Marketplace

Home Assistant 2026.11 replaced HACS with the built-in Marketplace. An installation made through
HACS moves over automatically and keeps receiving updates.

1. Go to **Settings > Marketplace** and select **Add from link**. This needs a GitHub connection.
2. Enter `pwsh/jriver_homeassistant` and select **Add**. If asked for a type, choose
   **Integration**.
3. Open **JRiver Media Center** and install version **2.0.2** or newer. Older versions do not
   load on Home Assistant 2026.11.
4. Restart Home Assistant if prompted.

## HACS

For Home Assistant 2026.10 or older.

1. In Home Assistant open **HACS**.
2. From the overflow menu choose **Custom repositories**.
3. Add the repository `https://github.com/pwsh/jriver_homeassistant` with the category
   **Integration**.
4. Search for **JRiver Media Center**, open it and choose **Download**. Pick version **2.0.0** or
   newer when HACS asks; the fork's `main` branch and its releases both carry the rework.
5. Restart Home Assistant. **Settings > Devices & Services > JRiver Media Center** should then
   show version 2.0.0 on the integration page.

{: .warning }
> If you already have the upstream **3ll3d00d** version installed through HACS or the
> Marketplace, remove it first. Both use the Home Assistant domain `jriver`, so Home Assistant
> will load only one of them and the result is undefined. Delete the upstream repository,
> restart, then install this fork. Your existing config entries, devices and entities are migrated
> automatically the first time the new version loads. See
> [Upgrading]({{ site.baseurl }}/upgrading/).

## Manual

Copy the `custom_components/jriver` directory from the `v2-rework` branch into your Home
Assistant `config/custom_components/` directory. Include the `mcws/` subdirectory.

```bash
git clone -b v2-rework https://github.com/pwsh/jriver_homeassistant.git
cp -r jriver_homeassistant/custom_components/jriver /path/to/config/custom_components/
```

Or download the branch as a zip from the repository's **Code > Download ZIP** menu with the
`v2-rework` branch selected, and copy `custom_components/jriver` out of it.

Restart Home Assistant afterwards.

## Add the integration

1. Go to **Settings > Devices & Services**.
2. Choose **Add integration** and search for **JRiver Media Center**.
3. Work through the setup flow described in
   [Configuration]({{ site.baseurl }}/configuration/).

## Removing the integration

Delete the config entry from **Settings > Devices & Services > JRiver Media Center**. All
devices, entities and history go with it. If you installed manually, also delete
`config/custom_components/jriver/`.
