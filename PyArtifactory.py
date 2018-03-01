import requests
import json
import yaml
import os

class Artifactory:
    def __init__(self, config_file):
        config = yaml.load(open('config.yml'))
        self.url = config['url']
        if 'username' in config:
            self.username = config['username']
        if 'password' in config:
            self.password = config['password']
        if 'api_key' in config:
            self.api_key = config['api_key']

    def authentication(self):
        if self.password:
            auth = (self.username, self.password)
            return auth
        if self.api_key:
            auth = (self.username, self.api_key)
            return auth

    def all_builds(self):
        url = "{base_url}/api/build/".format(base_url=self.url)
        all_builds_info = requests.get(url, auth=self.authentication())
        return all_builds_info.text

    def get_build_info(self, buildName, buildNumber):
        url = ("{base_url}/api/build/{build_name}/"
               "{build_number}").format(base_url=self.url,
                                        build_name=buildName,
                                        build_number=buildNumber)
        build_info = requests.get(url, auth=self.authentication())
        return build_info.text

    def get_latests_build_info(self, buildName, buildNumbers):
        result = []
        search_url = "{base_url}/api/search/aql".format(base_url=self.url)
        payload = 'builds.find({"name": "%s"})\
                  .sort({"$desc": ["number"]}).limit(%d)'\
                  % (buildName, buildNumbers)
        res = requests.post(search_url, data=payload,
                            auth=self.authentication())
        for i in json.loads(res.text)["results"]:
            self.get_build_info(buildName, i["build.number"])

    def search_build_artifacts(self, buildName, buildNumber):
        downloadUri = []
        search_url = ("{base_url}/api/search/"
                      "buildArtifacts").format(base_url=self.url)
        payload = {"buildName": buildName, "buildNumber": buildNumber}
        res = requests.post(search_url, json=payload,
                            auth=self.authentication())
        if "errors" in res.text:
            return 101
        for i in json.loads(res.text)["results"]:
            downloadUri.append(i["downloadUri"])
        return downloadUri

    def download_build(self, buildName, buildNumber):
        if self.search_build_artifacts(buildName, buildNumber) == 101:
            print("Could not find build !")
            return 0
        downloadUri = self.search_build_artifacts(buildName, buildNumber)
        for i in downloadUri:
            name = os.path.basename(i)
            r = requests.get(i, auth=self.authentication())
            with open(name, "wb") as out:
                out.write(r.content)

    def build_promotion(self, buildName, buildNumber, jsonFile):
        promoteUri = ("{base_url}/api/build/"
                      "promote/{build_name}"
                      "/{build_number}").format(base_url=self.url,
                                                build_name=buildName,
                                                build_number=buildNumber)
        json_file = json.load(open(jsonFile))
        request = requests.post(promoteUri, json=json_file,
                                auth=self.authentication())
        return request.text
