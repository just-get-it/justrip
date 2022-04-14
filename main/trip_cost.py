# trip cost cost = Base cost + km rate * traffic surge * route surge * fuel surge * (total distance-base distance) + (Ride time * (ride rate per min+entertainment rate per min)) + (Vehicle Waiting rate per minute + Driver waiting rate + Driver waiting allowance rate + Night Allowance rate)*(Trip duration: Ride time + waiting time) + ((Trip duration: Ride time+waiting time)/1440-1)*Driver Stay Allowance per day + (Toll + Permit + Parking) + (Justgetit Comission Convinienece rate % on sub final amount) + (5% GST of final amount)
from tokenize import group
from wallet.models import Wallet
from .models import *
import datetime
from django.contrib import messages


def time_in_range(start, end, current):
    """Returns whether current is in the range [start, end]"""
    return start <= current <= end


def get_traffic_surge(selected_pickup_time, charges):
    """Returns the Traffic Surge Cost based on pick-up time. You need to pass pickup-time and Charges-Obj."""
    # print("inside get_traffic_surge")
    now = datetime.datetime.now()
    # print(now.year, now.month, now.day, now.hour, now.minute, now.second)
    # print (f"{ now.hour }:{now.time}")
    pickup_time= selected_pickup_time if selected_pickup_time else f"{ now.hour }:{now.minute}"
    pickup_time = datetime.datetime.strptime(pickup_time, '%H:%M').time() 
    # print("pickup_time: ", pickup_time)
    nightBeg = datetime.time((12+10), 0)
    nightEnd = datetime.time(5, 0)
    morningBeg = datetime.time(9, 0, 0)
    eveningBeg = datetime.time((12+5), 0)
    morningEnd = datetime.time(11, 0)
    eveningEnd = datetime.time((12+8), 0)

    # print("nightBeg: ", nightBeg, "morningBeg: ", morningBeg, "eveningBeg: ", eveningBeg,
    #   "nightEnd: ", nightEnd, "morningEnd: ", morningEnd, "eveningEnd: ", eveningEnd)
    if time_in_range(nightBeg, nightEnd, pickup_time):
        return charges.night_traffic_surge_charge
    elif time_in_range(morningBeg, morningBeg, pickup_time):
        return charges.morning_traffic_surge_charge
    elif time_in_range(eveningBeg, eveningEnd, pickup_time):
        return charges.evening_traffic_surge_charge
    else:
        return 1


def get_route_surge(charges, drop_city="Mumbai",):
    """Returns the Route Surge based on drop city. You need to pass particular Charges object and drop-city."""
    routes = Route.objects.defer(None)

    for route in routes:
        if(route.destination.lower() == drop_city.lower()):
            if route.route_type == "A-I":
                # print(route.destination)
                # print("easy_I_route_surge",charges.easy_I_route_surge)
                return charges.easy_I_route_surge
            elif route.route_type == "A":
                # print(route.destination)
                # print("easy_I_route_surge",charges.easy_II_route_surge)
                return charges.easy_II_route_surge
            elif route.route_type == "B-I":
                # print(route.destination)
                # print("easy_I_route_surge",charges.remote_I_route_surge)
                return charges.remote_I_route_surge
            elif route.route_type == "B":
                # print(route.destination)
                # print("easy_I_route_surge",charges.remote_II_route_surge)
                return charges.remote_II_route_surge
    return 0


def get_fuel_surge(charges, pickup_city="mumbai", drop_city="bengaluru"):
    """Function returns fuel surge based on availabilty of fuel in the route according to priority. You need to pass charges obj, pickup-city and drop-cty"""
    # print("pickup_city: ",pickup_city,"drop_city: ",drop_city)
    try:
        route = Fuel_Route.objects.get(
            frm=pickup_city.lower(), to=drop_city.lower())
        # print("fuel_surge: ",route.fuel_type.defer(None))
        fuels = route.fuel_type.all().order_by('priority')
        for fuel in fuels:
            if fuel.fuel == "CNG":
                # print("cng_fuel_surge: ",charges.cng_fuel_surge)
                return charges.cng_fuel_surge
            elif fuel.fuel == "ELECTRIC":
                # print("electric_fuel_surge :",charges.electric_fuel_surge)
                return charges.electric_fuel_surge
            elif fuel.fuel == "DISEL":
                # print("disel_fuel_surge: ",charges.disel_fuel_surge)
                return charges.disel_fuel_surge
            elif fuel.fuel == "PETROL":
                # print("petrol_fuel_surge: ",charges.petrol_fuel_surge)
                return charges.petrol_fuel_surge
    except Charges.DoesNotExist:
        return 2
    except Exception as Arg:
        print("something went wrong", Arg)


def getCharges(request,vehicle_group, vehicle_type, trip_type, trip_variant, trip_way, distance, time, pickup_time, pickup_date, days, pickup_city, drop_city, waiting_time=30):
    """
    Function returns the Trip Cost

    Arguements:
    request, vehicle_type, trip_type, trip_variant, trip_way, distance, time, pickup_time, pickup_date, days, pickup_city, drop_city, waiting_time

    """
    print("inside get charges")
    print("days", days)
    details = detail.objects.filter(email=request.user.email).first() if request.user.is_authenticated else None
    owner = OwnerProfile.objects.filter(user=details).first() if request.user.is_authenticated else None
    profile = CustomerProfile.objects.filter(user=details).first() if request.user.is_authenticated else None
    wallet = Wallet.objects.filter(customer=profile).first() if request.user.is_authenticated else None
    try:
        # ************************ Getting Charges table ************************
        print(vehicle_type, "vehicle_type", "trip_type ", trip_type, " trip_variant ", trip_variant,
              " trip_way ", trip_way, "pickup_city ", pickup_city, " drop_city ", drop_city,"pickup_time ",pickup_time)
        charges = Charges.objects.get(
            car=vehicle_type, trip_type=trip_type, trip_variant=trip_variant, trip_way=trip_way)
        print("charges", charges)
        vehicle_type_obj = VehicalType.objects.get(name=vehicle_type,group=vehicle_group)
        print(charges.evening_traffic_surge_charge)

        # ************************ Basic Charges ************************

        if trip_way == "ROUND":
            distance = distance*2

        base_cost = charges.min_base_charge*int(days[0])
        Kms_covered_in_base_fare = charges.Kms_covered_in_base_fare * \
            int(days[0])
        km_rate = charges.rate_per_km
        print("rate per km ", charges.rate_per_km)
        minimum_km = charges.minimum_km*int(days[0])
        if minimum_km > distance:
            distance = minimum_km

        applicable_distance = distance - Kms_covered_in_base_fare
        applicable_charges = applicable_distance*km_rate

        ride_time = time
        if trip_way == "ROUND":
            time = time*2

        ride_rate_per_min = charges.ride_time_charge
        entertainment_rate_per_min = charges.entertainment_charge

        vehicle_waiting_rate_per_minute = charges.vehical_waiting_charge
        driver_waiting_rate = charges.driver_waiting_charge 
        driver_waiting_allowance_rate = charges.driver_waiting_allowances_charge 
        driver_waiting_night_allowances_rate = charges.driver_waiting_night_allowances_charge 

        trip_duration = ride_time+waiting_time
        driver_stay_allowance_per_day = charges.driver_waiting_stay_allowances_charge

        total_driver_allowance = driver_waiting_allowance_rate + \
            driver_waiting_night_allowances_rate+driver_stay_allowance_per_day

        # ************************ Trffic Surge ************************
        if trip_variant == "OUTSTATION" or trip_type == "SELF_DRIVING" or trip_type == "POOLING":
            traffic_surge = 1
        else:
            traffic_surge = get_traffic_surge(pickup_time, charges)

        # ************************ Route surge ************************
        route_surge_cost = get_route_surge(charges, drop_city)

        # ************************ Fuel Surge ************************
        fuel_surge_cost = get_fuel_surge(charges)

        total_surge = applicable_distance * \
            (traffic_surge+route_surge_cost+fuel_surge_cost)

        # ************************ Toll, Permit & Parking ************************
        # if data coming from web then use that

        obj = Toll_Permit_Parking.objects.filter(vehicle_group=vehicle_type_obj.group, route_from=pickup_city, route_to=drop_city).first()
        print("Toll permit & parking ", obj)
        if obj:
            toll = obj.toll
            permit = obj.permit
            parking = obj.parking
        else:
            toll = 0
            permit = 0
            parking = 0


        total_waiting_time=(vehicle_waiting_rate_per_minute + driver_waiting_rate+driver_waiting_allowance_rate+driver_waiting_night_allowances_rate)*waiting_time

        Trip_cost = base_cost 
        Trip_cost+= km_rate * traffic_surge * route_surge_cost * fuel_surge_cost*applicable_distance 
        Trip_cost+= ride_time * (ride_rate_per_min + entertainment_rate_per_min)
        Trip_cost+=(vehicle_waiting_rate_per_minute + driver_waiting_rate+driver_waiting_allowance_rate+driver_waiting_night_allowances_rate)*waiting_time
        Trip_cost+=((trip_duration)/1440-1)*driver_stay_allowance_per_day
        Trip_cost+=(toll+permit+parking)

        print("Trip_cost ", Trip_cost)
        # cupon is before GST
        coupons = None
        coupon_value = 0
        corporate_coupon = 0
        # if corporateuser then directly apply 10% flat coupon and ignore below coupon
        if profile and profile.is_corporate == True:
            corporate_coupon = Trip_cost*(10/100)
        else:
            try:
                coupons = Coupon.objects.filter(vehicle_group=vehicle_type_obj.group, vehicle_type=vehicle_type, trip_type=trip_type,trip_variant=trip_variant, trip_way=trip_way).order_by('-coupon_value')
                applied_coupon=coupons.first()
                print("coupon value", applied_coupon.coupon_value)
                trips_by_the_user=Trip.objects.filter(customer=profile,is_complete=True)
                print("trips_by_the_user ",trips_by_the_user)
                if trips_by_the_user:
                    pass
                coupon_value += applied_coupon.coupon_value
                print(coupon_value)

            except Exception as Arg:
                print("something went wrong", Arg)
        print("coupons ",coupons)
        # ************************ Just get it Convienience ************************
        print(vehicle_type_obj.conviniance_charge)
        conviniance_charge = Trip_cost*vehicle_type_obj.conviniance_charge/100
        Trip_cost += conviniance_charge

        # cash back wallet with some limit is before GST (coding is in old code)
        # noraml  wallet without any limit and or complete amount through payment gateway (refer old code)

        redeem_wallet=charges.redeem_wallet_percentage/100*Trip_cost
        justrip_money=0
        if wallet:
            justrip_money = wallet.balance
            redeem_wallet = min(wallet.redeem_balance,redeem_wallet)

        discounts = coupon_value+corporate_coupon+redeem_wallet

   

        # ************************ Effective Trip Cost ************************
        Effective_Trip_Cost = Trip_cost - discounts

        # ************************ GST ************************
        gst = Effective_Trip_Cost*0.05
        # ************************ Final trip cost ************************
        Final_Trip_Cost = Effective_Trip_Cost+gst
        print('\nFinal_Trip_Cost: ', Final_Trip_Cost)


        # pay later 100%, pay now 100% pay partial 25%
        # Cost to vendor 80% of trip cost, cost to driver to be 70% of the trip.
        # cash back after trip completion only to trip poster 0% - Normal customer, 10% - corporate, driver and vendor.
        cashback = 0
        if profile and profile.is_corporate == True:
            cashback = Final_Trip_Cost*10/100
        Final_Amount = Final_Trip_Cost-(cashback+justrip_money)
        print('\nFinal_Amount: ', Final_Amount)
        corporate_user=profile and profile.is_corporate == True
        trip_cost = {
            "base_cost": base_cost,
            "minimum_km": minimum_km,
            "rate_per_km": charges.rate_per_km,
            "total_distance": distance,
            "Kms_covered_in_base_fare": Kms_covered_in_base_fare,
            "applicable_distance": applicable_distance,
            "applicable_charges": applicable_charges,
            "ride_time": time,
            "days":days[0],
            "traffic_surge": traffic_surge,
            "fuel_surge_cost": fuel_surge_cost,
            "route_surge_cost": route_surge_cost,
            "ride_rate_per_min": ride_rate_per_min,
            "total_surge": total_surge,
            "vehicle_waiting_rate_per_minute": vehicle_waiting_rate_per_minute,
            "entertainment_rate_per_min": entertainment_rate_per_min,
            "driver_waiting_rate": driver_waiting_rate,
            "driver_waiting_allowance_rate": driver_waiting_allowance_rate,
            "night_allowance_rate": driver_waiting_night_allowances_rate,
            "total_waiting_time":total_waiting_time,
            "total_driver_allowance": total_driver_allowance,
            "trip_duration": trip_duration,
            "driver_stay_allowance_per_day": driver_stay_allowance_per_day,
            "waiting_time": waiting_time,
            "trip_duration":trip_duration,
            "parking":parking,
            "toll":toll,
            "permit":permit,
            "corporate":corporate_user,
            "corporate_coupon": corporate_coupon,
            "coupons":coupons,
            "coupon_value":coupon_value,
            "justrip_money": justrip_money,
            "redeem_wallet": redeem_wallet,
            "trip_cost": Trip_cost,
            "conviniance_charge": conviniance_charge,
            "Effective_Trip_Cost": Effective_Trip_Cost,
            "gst": gst,
            "Final_Trip_Cost": Final_Trip_Cost,
            "cost_to_vendor": Final_Trip_Cost*80/100,
            "cost_to_driver": Final_Trip_Cost*70/100,

        }
        return trip_cost
    except Charges.DoesNotExist as Arg:
        print(f"the {vehicle_type} charges is not exist")
        return None
    except VehicalType.DoesNotExist as Arg:
        print(f"The {vehicle_type} type vehical type is not exist")
        messages.warning(
            request, f"The {vehicle_type} type vehical service is not available, try others... ({Arg})")
        return None

    except Exception as Arg:
        print("something went wrong",Arg)
        messages.error(request, f'something went wrong ({Arg})')
        return None
