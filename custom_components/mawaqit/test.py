import os
os.system('pip3 install mawaqit_times_calculator')
from mawaqit_times_calculator import MawaqitTimesCalculator



mawaqit_login = "login here"
mawaqit_password = "password here"
mawaqit_latitude = "45.764043"
mawaqit_longitude = "4.835659"



 
calc = MawaqitTimesCalculator(
    mawaqit_latitude,
    mawaqit_longitude,
    '',
    mawaqit_login,
    mawaqit_password,
    ''
        )

print(calc.apimawaqit())
print(calc.fetch_prayer_times())
