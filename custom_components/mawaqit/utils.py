import json
import os

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


async def write_all_mosques_NN_file(mosques, hass):
    def write():
        with open("{}/data/all_mosques_NN.txt".format(CURRENT_DIR), "w") as f:
            json.dump(mosques, f)

    await hass.async_add_executor_job(write)


async def read_my_mosque_NN_file(hass):
    def read():
        with open("{}/data/my_mosque_NN.txt".format(CURRENT_DIR)) as f:
            mosque = json.load(f)
            return mosque

    return await hass.async_add_executor_job(read)


async def write_my_mosque_NN_file(mosque, hass):
    def write():
        with open("{}/data/my_mosque_NN.txt".format(CURRENT_DIR), "w") as f:
            json.dump(mosque, f)

    await hass.async_add_executor_job(write)


def create_data_folder():
    if not os.path.exists("{}/data".format(CURRENT_DIR)):
        os.makedirs("{}/data".format(CURRENT_DIR))


async def read_all_mosques_NN_file(hass):
    def read():
        name_servers = []
        uuid_servers = []
        CALC_METHODS = []

        with open("{}/data/all_mosques_NN.txt".format(CURRENT_DIR)) as f:
            dict_mosques = json.load(f)
            for mosque in dict_mosques:
                distance = mosque["proximity"]
                distance = distance / 1000
                distance = round(distance, 2)
                name_servers.extend([mosque["label"] + " (" + str(distance) + "km)"])
                uuid_servers.extend([mosque["uuid"]])
                CALC_METHODS.extend([mosque["label"]])

        return name_servers, uuid_servers, CALC_METHODS

    return await hass.async_add_executor_job(read)
