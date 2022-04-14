from django.shortcuts import render, redirect, HttpResponse,HttpResponseRedirect
from django.db.models import Q
from django.urls import reverse
from django.core import serializers
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import *
import json
from .forms import *
from django.contrib import messages
import requests
import datetime
from django.utils.timezone import now, timedelta
import razorpay
from wallet.models import *
from .utils import send_email, generateOTP6digit, randomStringDigits
from .trip_cost import getCharges
from Justrip.settings import EMAIL_HOST_USER
import pytz
from webpush import send_user_notification
from django.views.decorators.csrf import csrf_exempt
import geocoder
from threading import Timer
import time
import threading
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum
from django.db.models import Avg, Count
state_full_forms = { "an":"Andaman and Nicobar Islands","ap":"Andhra Pradesh","ar": "Arunachal Pradesh", "as": "Assam","br":"Bihar","ch":"Chandigarh"
,"ct":"Chhattisgarh","dn":"Dadra and Nagar Haveli","dd":"Daman and Diu","dl":"Delhi","ga":"Goa","gj":"Gujarat","hr":"Haryana","hp":"Himachal Pradesh","jk":"Jammu and Kashmir","jh":"Jharkhand","ka": "Karnataka","kl":"Kerala","ld":"Lakshadweep","mp":"Madhya Pradesh","mh":"Maharashtra","mn":"Manipur","ml":"Meghalaya","mz":"Mizoram","nl":"Nagaland","or":"Odisha","py":"Puducherry"
,"pb":"Punjab","rj":"Rajasthan","sk":"Sikkim","tn":"Tamil Nadu","tg":"Telangana","tr":"Tripura","up":"Uttar Pradesh","ut":"Uttarakhand","wb":"West Bengal"}
bing_key = 'AgB7hiqOcS-Xw-jNEegI1kq-LPI1BJPDRi5mlCfaLrs_0tBrOvsTTBpbJ4eSrEqo'
# User=get_user_model()
# Razorpay ID and Secret
razorpay_id = "rzp_live_048zfpCdwS3iFX"
razorpay_secret = "KclezNB6i7tv5h1UAU4U8AXp"

# mapbox_distance_base = 'https://api.mapbox.com/directions/v5/mapbox/driving/' + start[0] + ',' + start[1] + ';' + end[0] + ',' + end[1] + '?steps=true&geometries=geojson&access_token=' + mapboxgl.accessToken;
mapbox_distance_base = 'https://api.mapbox.com/directions/v5/mapbox/driving/'
mapbox_places_base = 'https://api.mapbox.com/geocoding/v5/mapbox.places/'
mapbox_key = 'pk.eyJ1IjoianVzdGNhYnMiLCJhIjoiY2toc241bG1xMHVsZDJxa3ozYnF3dXRsaCJ9.T2rWGRtN1od9-w0iIRFYjg'

payload = {
	"head": "Notification",
	"body": "This is a notification",
	"icon": "https://justcab.co.in/static/img/logo.png",
	"url": "https://justcab.co.in/dashboard/",
}

now = datetime.datetime.now()
hour = now.hour

if hour >= 9 and hour < 11:
	time_frame = "morning"
elif hour >= 11 and hour < 20:
	time_frame = "evening"
else:
	time_frame = "night"


today = datetime.datetime.today()
duration = today - datetime.datetime(2021,8,12,17,0,0,500)
num_days_from_start = divmod(duration.total_seconds(), 86400)[0]
print(int(num_days_from_start))
# trip.pickup_date = datetime.datetime.now()
# trip.save()
# status = Trip.objects.filter(trip_no = trip.trip_no)[0]
# if status.owner == None:
# 	print(trip.owner)
# else:
# 	print(trip.owner)
# def get_location_address(cordinates):
# 	cordinates_string = ','.join([str(elem) for elem in cordinates])
# 	url = mapbox_places_base + cordinates_string +'.json?access_token='+ mapbox_key +'&limit=1'
# 	print('get location url: {}'.format(url))
# 	r = requests.get(url)
# 	resp = r.json()
# 	features = resp.get('features')
# 	if not features:
# 		return "Invalid Address"
# 	addr = features[0].get('place_name')
# 	if addr:
# 		return addr
# 	else:
# 		loc = features[0].get('context')
# 		add = ''
# 		first = True
# 		for l in loc:
# 			temp = l.get('text')
# 			if temp:
# 				if first:
# 					add+= temp
# 				else:
# 					add += ', ' + temp
# 		add += '.'
# 		return add

def get_state_and_city(address):
	print("address",address)
	state = ''
	city = ''
	temp = address.split(',')
	print(temp, "tempppp")
	state_abbr = temp[-1].strip().split(' ')[0].lower()
	state = state_full_forms[state_abbr]
	city = temp[-2]
	city = city.strip()
	state = state.strip()
	print(city, state, "city, state")
	return city,state

def get_state_and_city_mapbox(address):
	state = ''
	city = ''
	temp = address.split(',')
	print(temp)
	state = temp[-2]
	city = temp[-3]
	city = city.strip()
	state = state.strip()
	return city, state

# def get_distance_and_time(start, end):
# 	start_string = ','.join([str(elem) for elem in start])
# 	end_string = ','.join([str(elem) for elem in end])
# 	url = mapbox_distance_base + start_string + ';' + end_string + '?access_token=' + mapbox_key
# 	print('get distance url: {}'.format(url))
# 	r = requests.get(url)
# 	resp = r.json()
# 	routes = resp.get('routes')
# 	if routes:
# 		distance = routes[0].get('distance')
# 		distance = int(distance)
# 		distance = distance / 1000
# 		time = routes[0].get('duration')
# 		time_in_hr = float(time)/3600
# 		return distance, time_in_hr
# 	else:
# 		return False


def get_location_address_mapbox(cordinates):
    cordinates_string = ','.join([str(elem) for elem in cordinates])
    url = mapbox_places_base + cordinates_string + \
        '.json?access_token=' + mapbox_key + '&limit=1'
    print('get location url: {}'.format(url))
    r = requests.get(url)
    resp = r.json()
    features = resp.get('features')
    if not features:
        return "Invalid Address"
    addr = features[0].get('place_name')
    if addr:
        return addr
    else:
        loc = features[0].get('context')
        add = ''
        first = True
        for l in loc:
            temp = l.get('text')
            if temp:
                if first:
                    add += temp
                else:
                    add += ', ' + temp
        add += '.'
        return add

# bing maps
def get_distance_and_time(start, end):		# my changes
	start.reverse()
	end.reverse()
	print(start, end)
	start_string = ','.join([str(elem) for elem in start])
	end_string = ','.join([str(elem) for elem in end])
	print(start_string, end_string)
	url = 'https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix?origins='+ end_string + '&destinations=' + start_string + '&travelMode=driving&key='+ bing_key
	r = requests.get(url)
	resp = (r.json())["resourceSets"][0]["resources"][0]
	print(resp)
	results = resp.get('results')
	if results :
		res = resp["results"][0]
		distance =  res["travelDistance"]
		time = res["travelDuration"]
		return abs(distance), abs(time)
	else:
		return False
		
# print(get_distance_and_time([77.5491,12.9847],[77.5772,13.0352]))

# bing maps
def get_location_address(cordinates):		# my changes
	print(cordinates)
	# cordinates.reverse()
	coordinates = ','.join([str(elem) for elem in cordinates])
	addr = geocoder.bing(coordinates, method = 'reverse', key = bing_key)
	addr_json = addr.json
	print(coordinates)
	print(addr_json)
	if addr_json:
		print(addr_json['address'])
		return addr_json['address']
	else: 
		return False
# get_location_address([77.5772,13.0352])

def save_user_current_location(request):		# my changes
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		customer = CustomerProfile.objects.filter(user=details).first() 
		owner = OwnerProfile.objects.filter(user=details).first()
		driver = DriverProfile.objects.filter(owner = owner).first()
		user_address = json.loads(request.body)['cur_address_coords']
		user_address_coord = user_address
		address_coords = user_address_coord.split(',')
		address_coords.reverse()
		# address = get_location_address(address_coords)
		if driver:
			# driver.current_location = address
			driver.cur_address_coords = address_coords
			driver.save()
		if owner:
			if owner.is_owner:
				print(owner, "owner object")
				owner.address_coords = address_coords
				# owner.address = address
				owner.save()
				print(owner, "owner object")
		if customer:
			customer.address = address_coords
			# customer.address_text = address
			customer.save()
	return JsonResponse({'result': 'ok'})
	# return render(request, 'index.html')

def get_pickup_drop_trip(request, trip_id):     # my changes
	trip_now = Trip.objects.get(pk = trip_id)
	print(trip_now)
	pickup_location = trip_now.pickup_location
	drop_location = trip_now.drop_location
	data = {
		'pickup_coords' : pickup_location,
		'drop_coords' : drop_location
	}
	return JsonResponse(data)

def get_live_location_coords(request, trip_id):     # my changes
	trip_now = Trip.objects.get(pk = trip_id)
	print(trip_now)
	driver_coords = trip_now.driver.cur_address_coords
	car_coords = trip_now.owner.address_coords
	customer_coords = trip_now.customer.address
	print(driver_coords, customer_coords, car_coords)
	data = {
		'driver_coords':driver_coords,
		'car_coords':car_coords,
		'customer_coords':customer_coords
	}
	return JsonResponse(data)
	# return HttpResponse(json.dumps(data), content_type='application/json')

# def graph_data(labels, data):
# 	data = {
# 		"labels":labels,
# 		"data":data
# 	}
# 	return JsonResponse(data)

def admin_charts(request):
	details = detail.objects.filter(email=request.user.email).first()
	owner = OwnerProfile.objects.filter(user=details).first()
	profile = CustomerProfile.objects.filter(user=details).first()
	user = request.user
	if owner:
		if owner.is_owner:
			return redirect('owner_dashboard')
		else:
			return redirect('vendor_dashboard')
	elif profile:
		return redirect('customer_dashboard')
	if details:
		if details.is_staff:
			staff = True
		else:
			staff = False
	else:
		staff = False
	if request.user.is_superuser or staff:
		today = datetime.datetime.today()
		labels = ["Today", "Daily Avg"]

		trip_everyday = Trip.objects.all().extra({'date_created' : "date(booking_date)"}).values('date_created').annotate(created_count=Count('id'))
		trip_sum = 0
		for i in trip_everyday:
			trip_sum += i['created_count']
		trip_avg = trip_sum/num_days_from_start
		trip_today_count = Trip.objects.filter(booking_date = today ).count()
		trip_graph_data = [trip_today_count, trip_avg]

		all_customers = CustomerProfile.objects.all()
		users = []
		for i in all_customers:
			users.append(User.objects.filter(email = i.user.email)[0].email)
		customer_everyday = User.objects.filter(email__in = users).extra({'date_created' : "date(date_joined)"}).values('date_created').annotate(created_count=Count('id'))
		customer_sum = 0
		for i in customer_everyday:
			customer_sum += i['created_count']
		customer_avg = customer_sum/num_days_from_start
		customer_today_count = User.objects.filter(date_joined = today ).count()
		customer_graph_data = [customer_today_count, customer_avg]

		all_drivers = DriverProfile.objects.all()
		users = []
		for i in all_drivers:
			users.append(User.objects.filter(email = i.owner.user.email)[0].email)
		driver_everyday = User.objects.filter(email__in = users).extra({'date_created' : "date(date_joined)"}).values('date_created').annotate(created_count=Count('id'))
		driver_sum = 0
		for i in driver_everyday:
			driver_sum += i['created_count']
		driver_avg = driver_sum/num_days_from_start
		driver_today_count = User.objects.filter(date_joined = today ).count()
		driver_graph_data = [driver_today_count, driver_avg]

		all_owners = OwnerProfile.objects.all()
		users = []
		for i in all_owners:
			users.append(User.objects.filter(email = i.user.email)[0].email)
		owner_everyday = User.objects.filter(email__in = users).extra({'date_created' : "date(date_joined)"}).values('date_created').annotate(created_count=Count('id'))
		owner_sum = 0
		for i in owner_everyday:
			owner_sum += i['created_count']
		owner_avg = owner_sum/num_days_from_start
		owner_today_count = User.objects.filter(date_joined = today ).count()
		owner_graph_data = [owner_today_count, owner_avg]

		car_everyday = Car.objects.all().extra({'date_created' : "date(registered_on)"}).values('date_created').annotate(created_count=Count('id'))
		car_sum = 0
		for i in car_everyday:
			car_sum += i['created_count']
		car_avg = car_sum/num_days_from_start
		car_today_count = Car.objects.filter(registered_on = today ).count()
		car_graph_data = [car_today_count, car_avg]
		
		data = {
			"labels":labels,
			"trip_graph_data":trip_graph_data,
			"customer_graph_data":customer_graph_data,
			"driver_graph_data":driver_graph_data,
			"owner_graph_data":owner_graph_data,
			"car_graph_data":car_graph_data,
		}
		return render(request, 'admin_charts.html',data)

def admin_track_trip(request, trip_id):     # my changes
	details = detail.objects.filter(email=request.user.email).first()
	owner = OwnerProfile.objects.filter(user=details).first()
	profile = CustomerProfile.objects.filter(user=details).first()
	user = request.user
	if owner:
		if owner.is_owner:
			return redirect('owner_dashboard')
		else:
			return redirect('vendor_dashboard')
	elif profile:
		return redirect('customer_dashboard')
	if details:
		if details.is_staff:
			staff = True
		else:
			staff = False
	else:
		staff = False
	if request.user.is_superuser or staff:
		data = {
			'trip_id': trip_id,
		}
		return render(request, 'admin_track_trip.html',data)

def notification_detail(request, trip_id):
	if request.user.is_authenticated:		# my changes
		print(trip_id)
		this_trip = Trip.objects.filter(pk=trip_id).first()	
		print(this_trip)
		data = {
			'trip': this_trip,
		}
		# this_notification = Notification.objects.filter(link_id = trip_id).first()
		# this_notification.seen = True
		# this_notification.save()
		# print(this_notification)
		return render(request, 'notification_detail.html',data)

def owner_accept_trip(request):		# my changes
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		owner_driver = owner.drivers.filter(is_verified=True).first()
		owner_car = owner.cars.filter(is_verified=True).first()
		print(request.body)
		trip_id = json.loads(request.body)["accept"]
		trip = Trip.objects.get(id=trip_id)
		trip.owner = owner
		trip.driver = owner_driver
		trip.car = owner_car
		if not trip.start_otp:
			trip.generate_otp()
		trip.save()
		e = Event(
			trip = trip,
			username = owner.user.name,
			email = owner.user.email,
			text = 'Trip accepted by ' + owner.user.name
		)
		e.save()
		messages.success(request, 'Trip Accepted Successfully')
		return redirect('owner_my_trips')

def owner_reject_trip(request):
	if request.user.is_authenticated:
		trip_id = json.loads(request.body)["reject"]
		this_notification = Notification.objects.filter(link_id = trip_id).first()
		this_notification.seen = True
		this_notification.save()
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		trip = Trip.objects.get(id=trip_id)
		trip.rejected_by.add(owner)
		trip.save()
		e = Event(
			trip = trip,
			username = owner.user.name,
			email = owner.user.email,
			text = 'Trip rejected by ' + owner.user.name 
		)
		e.save()
		messages.success(request, 'Trip removed')
		return redirect('owner_my_trips')

class RepeatTimer(Timer):
	def run(self):
		while not self.finished.wait(self.interval):
			trip = self.args
			trip_owner = Trip.objects.filter(trip_no = trip.trip_no)[0]
			trip_status = trip_owner.owner
			if trip_status != None:
				self.function(*self.args, **self.kwargs)

def send_notification(trip):
	pickup_state = State.objects.filter(name=trip.pickup_state).first()
	drop_state = State.objects.filter(name=trip.drop_state).first()
	print(pickup_state, drop_state)
	eligible_vendors = OwnerProfile.objects.filter(states__in = [pickup_state, drop_state])
	notification_text = 'Pickup: {} Drop: {} on {}, Amount: {}'.format(trip.pickup_city, trip.drop_city, trip.pickup_date, trip.vendor_amount)
	available_drivers = DriverProfile.objects.filter(is_verified=True)
	min_dist_vendor_pickup = []		
	print(trip.pickup_location, "trip location in notification")
	pickup_cordinates = [str(x) for x in trip.pickup_location]
	pickup_cordinates.reverse()	
	print(pickup_cordinates, "trip cordinates in notification")
	drop_cordinates = [str(x) for x in trip.drop_location]
	drop_cordinates.reverse()	
	print(eligible_vendors, "eligible_vendors in notification")
	print(available_drivers, "available_drivers in notification")
	dirver_request = DriverProfile.objects.filter(has_requested=True)
	now = datetime.datetime.now()	
	print(now)
	pickup_time = datetime.datetime.combine(trip.pickup_date, trip.pickup_time) 
	time_gap = pickup_time - datetime.datetime.combine(trip.booking_date, trip.booking_time) 
	hours_gap = time_gap.days* 24 + time_gap.seconds/3600
	current_time_left = pickup_time - now 
	hours_left = current_time_left.days* 24 + current_time_left.seconds/3600
	if dirver_request.count() > 0:
		if hours_left <= hours_gap and hours_left > hours_gap*(1/2):
			for driver_home in dirver_request:
				driver_home_cordinates = [str(x) for x in driver_home.home_loc_coords]
				driver_home_cordinates.reverse()
				driver_home_dist, time = get_distance_and_time(drop_cordinates, driver_home_cordinates ) 
				print(driver_home_dist, "driver_home_dist in notifications")
				if driver_home_dist < 25:
					for vendor in eligible_vendors: # iterate throught vendors 
						vendor_cordinates = [str(x) for x in vendor.address_coords]
						vendor_cordinates.reverse()	
						print(vendor_cordinates)
						dist_vendor_pickup, time = get_distance_and_time(pickup_cordinates, vendor_cordinates ) 
						print(dist_vendor_pickup,time)
						for driver in dirver_request:
							driver_cordinates = [str(x) for x in driver.request_loc_coords]
							driver_cordinates.reverse()		# given current_location is location coordinates
							dist_driver_vendor, time = get_distance_and_time(vendor_cordinates, driver_cordinates)
							min_dist_vendor_pickup.append([vendor, dist_vendor_pickup, driver, dist_driver_vendor])
					sorted_min_dist_vendor_pickup = sorted(min_dist_vendor_pickup, key = lambda x: x[1] + x[3])
					print(sorted_min_dist_vendor_pickup) 
					for vendor in sorted_min_dist_vendor_pickup:	# iterate through sorted list and send notification to nearest vendor and driver combination				
						vendor_dist = vendor[1]
						driver_dist = vendor[3]
						chosen_vendor = vendor[0]
						if vendor_dist + driver_dist <= 25:
							chosen_vendor = vendor[0]
							print(chosen_vendor)
							n = Notification(
								to = chosen_vendor.user,
								text = notification_text,
								link_id = trip.id,
								booking = True,
								# user = chosen_vendor.user
							)
							n.save()
							print(n,"notification object saved")
							user = User.objects.filter(email=chosen_vendor.user.email).first()
							payload['head'] = "New Trip"
							payload['body'] = notification_text
							send_user_notification(user=user, payload=payload, ttl=86400)
	if hours_left <= hours_gap*(1/2) or dirver_request.count() == 0:
		print(dirver_request, "driver request none")
		for vendor in eligible_vendors: # iterate throught vendors 
			vendor_cordinates = [str(x) for x in vendor.address_coords]
			vendor_cordinates.reverse()	
			print(vendor_cordinates, "vendor_cordinates in notification")

			dist_vendor_pickup, time = get_distance_and_time(pickup_cordinates, vendor_cordinates ) 
			print(dist_vendor_pickup,time, "dist_vendor_pickup in notification")
			for driver in available_drivers:
				driver_cordinates = [str(x) for x in driver.cur_address_coords]
				driver_cordinates.reverse()		# given current_location is location coordinates
				dist_driver_vendor, time = get_distance_and_time(vendor_cordinates, driver_cordinates) 
				min_dist_vendor_pickup.append([vendor, dist_vendor_pickup, driver, dist_driver_vendor])
		sorted_min_dist_vendor_pickup = sorted(min_dist_vendor_pickup, key = lambda x: x[1] + x[3])
		print(sorted_min_dist_vendor_pickup)
		
		for vendor in sorted_min_dist_vendor_pickup:	# iterate through sorted list and send notification to nearest vendor and driver combination				
			vendor_dist = vendor[1]
			driver_dist = vendor[3]
			chosen_vendor = vendor[0]
			if hours_left <= hours_gap and hours_left > hours_gap*(4/5):
				if vendor_dist + driver_dist <= 5:
					chosen_vendor = vendor[0]
			elif hours_left <= hours_gap*(4/5) and hours_left > hours_gap*(3/5):
				if vendor_dist + driver_dist > 5 and vendor_dist + driver_dist <= 10:
					chosen_vendor = vendor[0]
			elif hours_left <= hours_gap*(3/5) and hours_left > hours_gap*(2/5):
				if vendor_dist + driver_dist > 10 and vendor_dist + driver_dist <= 15:
					chosen_vendor = vendor[0]
			elif hours_left <= hours_gap*(2/5) and hours_left > hours_gap*(1/5):
				if vendor_dist + driver_dist > 15 and vendor_dist + driver_dist <= 20:
					chosen_vendor = vendor[0]
			elif hours_left <= hours_gap*(1/5):
				if vendor_dist + driver_dist > 20:
					chosen_vendor = vendor[0]
			
			print(chosen_vendor)
			n = Notification(
				to = chosen_vendor.user,
				text = notification_text,
				link_id = trip.id,
				booking = True,
				# user = chosen_vendor.user
			)
			n.save()
			print(n,"notification object saved")
			user = User.objects.filter(email=chosen_vendor.user.email).first()
			payload['head'] = "New Trip"
			payload['body'] = notification_text
			send_user_notification(user=user, payload=payload, ttl=86400)

def notification_for_trips(trip):
	pickup_time = datetime.datetime.combine(trip.pickup_date, trip.pickup_time) 
	time_gap = pickup_time - datetime.datetime.combine(trip.booking_date, trip.booking_time) 
	hours_gap = time_gap.days* 24 + time_gap.seconds/3600
	send_notification(trip)
	print("notification sent")
	notification_timer = RepeatTimer((hours_gap*3600)/5, send_notification, args=(trip))
	notification_timer.start()
	time.sleep(hours_gap*3600)
	notification_timer.cancel()

# threading.Thread(target=dum).start()
# Create your views here.


def terms_and_conditions(request):
    return render(request, 'terms_and_conditions.html')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def contact_us(request):
    return render(request, 'contact_us.html')


def index(request):
	return render(request, 'index.html')


def notifications(request):
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		customer = CustomerProfile.objects.filter(user=details).first()
		if owner:
			if owner.is_owner:
				template = 'owner_notifications.html'
			elif owner.is_vendor:
				template = 'vendor_notifications.html'
		if customer:
			template = 'customer_notifications.html'
		if request.user.is_superuser or details.is_staff:
			template = 'admin_notifications.html'
		if request.user.is_superuser:
			all_notifications = request.user.admin_notifications.all().order_by('-date')
		else:
			all_notifications = details.notifications.all().order_by('-date')
			print(all_notifications)
			link_ids = []
			for i in all_notifications:
				link_ids.append(i.link_id) 
			all_trip = Trip.objects.filter(id__in = link_ids)
			print(all_trip)
			owner_driver = owner.drivers.filter(is_verified=True).first()
			owner_car = owner.cars.filter(is_verified=True).first()
			if not owner_driver or not owner_car or not owner.is_active:
				verified = False
			else:
				verified = True
			if request.POST.get('reject'):
				trip_id = request.POST.get('reject')
				trip = Trip.objects.get(pk=trip_id)
				trip.rejected_by.add(owner)
				trip.save()
				e = Event(
					trip = trip,
					username = owner.user.name,
					email = owner.user.email,
					text = 'Trip rejected by ' + owner.user.name 
				)
				e.save()
				messages.success(request, 'Trip removed')
				return redirect('owner_home')
			if request.POST.get('accept'):
				trip_id = request.POST.get('accept')
				trip = Trip.objects.get(pk=trip_id)
				trip.owner = owner
				trip.driver = owner_driver
				trip.car = owner_car
				if not trip.start_otp:
					trip.generate_otp()
				trip.save()
				e = Event(
					trip = trip,
					username = owner.user.name,
					email = owner.user.email,
					text = 'Trip accepted by ' + owner.user.name
				)
				e.save()
				messages.success(request, 'Trip Accepted Successfully')
				return redirect('owner_active_bookings')
			all_trips = []
			wallets = []
			owner_states = []
			for state in owner.states.all():
				owner_states.append(state.name)
			for i in all_trip:
				wallets = Wallet.objects.get(customer = i.customer)
				if i.pickup_state in owner_states or i.drop_state in owner_states:
					all_trips.append([i,wallets,True])
			one_way_trips = Trip.objects.filter(round_trip = False)
			one_way_amount = one_way_trips.aggregate(Sum('bill_amount'))['bill_amount__sum']
			one_way = one_way_trips.count()
			round_trips = Trip.objects.filter(round_trip = True)
			round_trip_amount = round_trips.aggregate(Sum('bill_amount'))['bill_amount__sum']
			round_trip = round_trips.count()
			if round_trip == 0:
				round_trip_amount = 0	
			if one_way == 0:
				one_way_amount = 0	

			print(one_way, "number of trips")
		return render(request, template, {'notify': all_notifications, 'trips': all_trips, 'verified': verified, 'wallet': wallets, 'one_way':one_way, 'round_trip':round_trip, 'one_way_amount':one_way_amount, 'round_trip_amount':round_trip_amount})
	else:
		return redirect('login_page')

@csrf_exempt
def ajax_request(request):
    if request.user.is_authenticated:
        if request.POST.get('action') == 'notifications_viewed':
            if request.user.is_superuser:
                notify = request.user.admin_notifications.filter(seen=False)
            else:
                details = detail.objects.filter(
                    email=request.user.email).first()
                notify = details.notifications.filter(seen=False)
            for n in notify:
                n.seen = True
                n.save()
            return JsonResponse({"success": True})
    else:
        return redirect('login_page')


def login_page(request):
	data={
	"invalid":False
	}
	redirect_to = request.GET.get('next')
	data['redirect_url'] = redirect_to	
	print(f'\n\nRE: {redirect_to}\n\n')
	if request.POST:
		postData = json.loads(request.body)
		email=postData['email']
		password=postData['password']
		current_user = User.objects.get(username=email)
		check_user = check_password(password,current_user.password)
		print(check_user, "user status")
		if check_user is True:
			user=User.objects.get(username=email)
			print('USER',user)
			login(request,user)
			if user.is_superuser:
				data['url'] = '/admin_dashboard'
			user=detail.objects.filter(email=request.user.email)
			if user.count()>0:
				user=user.first()
				profile = OwnerProfile.objects.filter(user=user).first()
				customer = CustomerProfile.objects.filter(user=user).first()
				if profile:
					wallet = profile.wallet.first()
					if not wallet:
						wallet = Wallet(owner=profile, deactivate_amount = 1000, is_active=True)
						wallet.save()
					if profile.is_owner:
						data['url'] = '/owner_home'
					elif profile.is_vendor:
						data['url'] = '/vendor_home'
				if customer:
					wallet = customer.wallet.first()
					if not wallet:
						wallet = Wallet(customer=customer, is_active=True)
						wallet.save()
					data['url'] = '/customer_create_trip'
				if user.is_staff:
					data['url'] = '/admin_dashboard'
			if redirect_to:
				data['url'] = redirect_to
			return HttpResponse(json.dumps(data), content_type='application/json')
		else:
			data['invalid'] = True
			data['url'] = '/login'
			return HttpResponse(json.dumps(data), content_type='application/json')
	return render(request,"login.html",data)

def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('login_page')


def recover(request):
    data = {
        "invalid": False
    }
    if request.POST.get('email') or request.user.is_authenticated:
        if request.POST.get('email'):
            user = User.objects.filter(email=request.POST.get('email')).first()
            deta = detail.objects.filter(
                email=request.POST.get('email')).first()
        else:
            user = User.objects.filter(email=request.user.email).first()
            deta = detail.objects.filter(email=request.user.email).first()
        if user and deta:
            # subject,message,from_email,to_list
            subject = "Password Recovery !"
            otp = generateOTP6digit()
            deta.user_otp = otp
            deta.user_otp_time = datetime.datetime.now()
            key = randomStringDigits()
            deta.user_otp_key = key
            deta.save()
            message = "Hey "+deta.name+"\n\n\nYour OTP verification code is " + \
                str(otp)+"\n\n\nThanks & Regards\nRaymond Institutional Team"
            from_email = EMAIL_HOST_USER
            to_list = [deta.email]
            send_email(subject, message, from_email, to_list)
            # return redirect('/userdetail/recover/otp?c='+str(key))
            return redirect(('{}?c='+str(key)).format(reverse('revover_otp')))
        else:
            data["invalid"] = True
    return render(request, "recover.html", data)


def recover_otp(request):
    check = False
    utc = pytz.UTC
    if request.GET.get('c') or request.POST.get('c'):
        if request.GET.get('c'):
            deta = detail.objects.filter(
                user_otp_key=request.GET.get('c')).first()
            if deta:
                check = True
        elif request.POST.get('c'):
            deta = detail.objects.filter(
                user_otp_key=request.GET.get('c')).first()
            if deta:
                check = True
    if check:
        data = {
            "invalid": False
        }
        if request.POST.get('c') and request.POST.get('otp'):
            key = deta.user_otp_key
            start_time = deta.user_otp_time
            end_time = start_time + datetime.timedelta(minutes=5)
            cur_time = timezone.now()
            otp = request.POST.get('otp')
            if cur_time > start_time and cur_time < end_time and deta.user_otp == otp:
                deta.user_otp_verify = datetime.datetime.now()
                key = randomStringDigits()
                deta.user_otp_key = key
                deta.save()
                return redirect('recover_password', key=str(key))
            else:
                data["invalid"] = True
        return render(request, "recover_otp.html", data)
    else:
        return redirect('/')


def recover_password(request, key):
    utc = pytz.UTC
    deta = detail.objects.filter(user_otp_key=key).first()
    if deta:
        if deta.user_otp_verify:
            start_time = deta.user_otp_verify
            end_time = start_time + datetime.timedelta(minutes=5)
            cur_time = timezone.now()
            if cur_time > start_time and cur_time < end_time:
                data = {
                    "invalid": False
                }
                if request.POST.get('new_password') and request.POST.get('confirm_password'):
                    new = request.POST.get('new_password')
                    confirm = request.POST.get('confirm_password')
                    if new != confirm:
                        data["invalid"] = True
                        return render(request, "recover_password.html", data)
                    else:
                        user = User.objects.filter(email=deta.email).first()
                        if user:
                            user.set_password(new)
                            user.save()
                            deta.password = new
                            deta.save()
                            return redirect('/')
                        else:
                            return redirect('/')
                return render(request, "recover_password.html", data)
            else:
                return redirect('/')
        else:
            return redirect('/')
    else:
        return redirect('/')


def dashboard(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if owner:
            if owner.is_owner:
                return redirect('owner_home')
            elif owner.is_vendor:
                return redirect('vendor_home')
        if customer:
            return redirect('customer_create_trip')
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        else:
            return redirect('index')
    else:
        return redirect('login_page')


def register_owner(request):
    data = {
        "exist": False,
        "owner": True,
    }
    if request.POST:
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        contact = request.POST.get('contact')
        gender = request.POST.get('gender')
        user = User.objects.filter(email=email)
        if user.count() > 0:
            data = {
                "exist": True
            }
        else:
            user = User.objects.create_user(
                email=email,
                username=email,
                password=password)
            user1 = detail(
                name=name,
                email=email,
                password=password,
                contact=contact,
                gender=gender,
            )
            user1.save()
            owner_profile = OwnerProfile(
                user=user1,
                is_owner=True,
            )
            owner_profile.save()
            wallet = Wallet(owner=owner_profile,
                            deactivate_amount=1000, is_active=True)
            wallet.save()
            e = Event(
                owner=owner_profile,
                username=owner_profile.user.name,
                email=owner_profile.user.email,
                text='Profile was created'
            )
            e.save()
            admins = User.objects.filter(is_superuser=True)
            staffs = detail.objects.filter(is_staff=True)
            for admin in admins:
                n = Notification(
                    user=admin,
                    text='New owner account has been created!',
                    link_id=owner_profile.id,
                    owner_profile=True,
                )
                n.save()
                payload['head'] = "Owner Account"
                payload['body'] = "New owner account has been created!"
                send_user_notification(user=admin, payload=payload, ttl=86400)
            for staff in staffs:
                n = Notification(
                    to=staff,
                    text='New owner account has been created!',
                    link_id=owner_profile.id,
                    owner_profile=True
                )
                n.save()
                user = User.objects.filter(email=staff.email).first()
                payload['head'] = "Owner Account"
                payload['body'] = "New owner account has been created!"
                send_user_notification(user=user, payload=payload, ttl=86400)
            messages.success(
                request, 'Welcome to Justrip, you have successfully registered as a owner')
            return redirect('login_page')
    return render(request, "register.html", data)


def register_customer(request):
	data={
	"exist":False,
	"customer": True
	}
	if request.POST:
		name=request.POST.get('name')
		email=request.POST.get('email')
		password=request.POST.get('password')
		contact=request.POST.get('contact')
		gender=request.POST.get('gender')
		user=User.objects.filter(email=email)
		if user.count()>0:
			data={
			"exist":True
			}
		else:
			user=User.objects.create_user(
				email=email,
				username=email,
				password=password)
			user1=detail(
				name=name,
				email=email,
				password=password,
				contact=contact,
				gender=gender,
			)
			print(user1.name, user1.email, user1.password, user1.contact, user1.gender)
			user1.save()
			cust_profile = CustomerProfile(
				user = user1,
			)
			cust_profile.save()
			wallet = Wallet(customer=cust_profile, redeem_balance=1000, is_active=True)
			wallet.save()
			e = Event(
				customer = cust_profile,
				username = cust_profile.user.name,
				email = cust_profile.user.email,
				text = 'Profile was created'
			)
			e.save()
			admins = User.objects.filter(is_superuser=True)
			staffs = detail.objects.filter(is_staff=True)
			for admin in admins:
				n = Notification(
					user = admin,
					text = 'New customer account has been created!',
					link_id = cust_profile.id,
					customer_profile = True,
				)
				n.save()
				payload['head'] = "Customer Account"
				payload['body'] = "New customer account has been created!"
				send_user_notification(user=admin, payload=payload, ttl=86400)
			for staff in staffs:
				n = Notification(
					to = staff,
					text = 'New customer account has been created!',
					link_id = cust_profile.id,
					customer_profile = True
				)
				n.save()
				user = User.objects.filter(email=staff.email).first()
				payload['head'] = "Customer Account"
				payload['body'] = "New customer account has been created!"
				send_user_notification(user=user, payload=payload, ttl=86400)
			messages.success(request, 'Welcome to Justrip, you have successfully registered as a customer')
			return redirect('login_page')
	return render(request,"register_customer.html",data)

def register_corporate_customer(request):
	data={
	"exist":False,
	"customer": True
	}
	if request.POST:
		name=request.POST.get('name')
		email=request.POST.get('email')
		password=request.POST.get('password')
		contact=request.POST.get('contact')
		gender=request.POST.get('gender')
		user=User.objects.filter(email=email)
		if user.count()>0:
			data={
			"exist":True
			}
		else:
			user=User.objects.create_user(
				email=email,
				username=email,
				password=password)
			user1=detail(
				name=name,
				email=email,
				password=password,
				contact=contact,
				gender=gender,
			)
			print(user1.name, user1.email, user1.password, user1.contact, user1.gender)
			user1.save()
			cust_profile = CustomerProfile(
				user = user1,
				is_corporate = True
			)
			cust_profile.save()
			wallet = Wallet(customer=cust_profile, redeem_balance=1000, is_active=True)
			wallet.save()
			e = Event(
				customer = cust_profile,
				username = cust_profile.user.name,
				email = cust_profile.user.email,
				text = 'Profile was created'
			)
			e.save()
			corporate_cust = CorporateCustomerProfile(
				user = cust_profile,
				gst = request.POST.get('gst'),
				pan = request.POST.get('pan'),
				pan_image = request.FILES.get('pan_pic')
			)
			corporate_cust.save()
			admins = User.objects.filter(is_superuser=True)
			staffs = detail.objects.filter(is_staff=True)
			for admin in admins:
				n = Notification(
					user = admin,
					text = 'New customer account has been created!',
					link_id = cust_profile.id,
					customer_profile = True,
				)
				n.save()
				payload['head'] = "Customer Account"
				payload['body'] = "New customer account has been created!"
				send_user_notification(user=admin, payload=payload, ttl=86400)
			for staff in staffs:
				n = Notification(
					to = staff,
					text = 'New customer account has been created!',
					link_id = cust_profile.id,
					customer_profile = True
				)
				n.save()
				user = User.objects.filter(email=staff.email).first()
				payload['head'] = "Customer Account"
				payload['body'] = "New customer account has been created!"
				send_user_notification(user=user, payload=payload, ttl=86400)
			messages.success(request, 'Welcome to Justrip, you have successfully registered as a customer')
			return redirect('login_page')
	return render(request,"register_corporate_customer.html",data)

def register_vendor(request):
    data = {
        "exist": False,
        "vendor": True,
    }
    if request.POST:
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        contact = request.POST.get('contact')
        gender = request.POST.get('gender')
        user = User.objects.filter(email=email)
        if user.count() > 0:
            data = {
                "exist": True
            }
        else:
            user = User.objects.create_user(
                email=email,
                username=email,
                password=password)
            user1 = detail(
                name=name,
                email=email,
                password=password,
                contact=contact,
                gender=gender,
            )
            user1.save()
            cab_profile = OwnerProfile(
                user=user1,
                is_vendor=True,
            )
            cab_profile.save()
            wallet = Wallet(owner=cab_profile, is_active=True,
                            deactivate_amount=1000)
            wallet.save()
            e = Event(
                owner=cab_profile,
                username=cab_profile.user.name,
                email=cab_profile.user.email,
                text='Profile was created'
            )
            e.save()
            admins = User.objects.filter(is_superuser=True)
            staffs = detail.objects.filter(is_staff=True)
            for admin in admins:
                n = Notification(
                    user=admin,
                    text='New vendor account has been created!',
                    link_id=cab_profile.id,
                    owner_profile=True,
                )
                n.save()
                payload['head'] = "Vendor Account"
                payload['body'] = "New vendor account has been created!"
                send_user_notification(user=admin, payload=payload, ttl=86400)
            for staff in staffs:
                n = Notification(
                    to=staff,
                    text='New vendor account has been created!',
                    link_id=cab_profile.id,
                    owner_profile=True
                )
                n.save()
                user = User.objects.filter(email=staff.email).first()
                payload['head'] = "Vendor Account"
                payload['body'] = "New vendor account has been created!"
                send_user_notification(user=user, payload=payload, ttl=86400)
            messages.success(
                request, 'Welcome to Justrip, you have successfully registered as a vendor')
            return redirect('login_page')
    return render(request, "register.html", data)


def staff_registration(request):
    data = {
        "exist": False,
        "staff": True
    }
    if request.POST:
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        contact = request.POST.get('contact')
        gender = request.POST.get('gender')
        user = User.objects.filter(email=email)
        if user.count() > 0:
            data = {
                "exist": True
            }
        else:
            user = User.objects.create_user(
                email=email,
                username=email,
                password=password)
            user1 = detail(
                name=name,
                email=email,
                password=password,
                contact=contact,
                gender=gender,
                is_staff=True
            )
            profile = user1.save()
            e = Event(
                user=profile,
                username=profile.name,
                email=profile.email,
                text='Profile was created'
            )
            e.save()
            messages.success(
                request, 'Welcome to Justrip, you have successfully registered as a staff')
            return redirect('login_page')
    return render(request, "register.html", data)


def owner_details(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        profile = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if profile.is_vendor:
            vendor = True
        else:
            vendor = False
        if request.POST.get('profile_pic_update'):
            profile.profile_picture = request.FILES.get('profile_pic')
            profile.save()
            e = Event(
                owner=profile,
                username=profile.user.name,
                email=profile.user.email,
                text='Profile picture updated by owner'
            )
            e.save()
            messages.success(request, 'Profile picture updated successfully')
            return redirect('owner_details')
        if request.POST.get('address_coords'):
            address_location = request.POST.get('address_coords')
            address_coords = address_location.split(',')
            print(f'ADD COORD: {address_coords}')
            address_coords.reverse()
            address = get_location_address(address_coords)
            print(f'ADDR: {address}')
            if address == 'Invalid Address':
                messages.error(request, 'Please Select Valid Address')
                return redirect('owner_details')
            # Saving Updated Data
            city, state = get_state_and_city(address)
            profile.address_coords = address_coords
            profile.state = state
            print(f'STATE: {state} CITY: {city}')
            obj_state = State.objects.filter(name=state).first()
            if obj_state:
                profile.states.add(obj_state)
            else:
                messages.error(request, 'Please Select Valid Address')
                return redirect('owner_details')
            profile.address = address
            profile.save()
            e = Event(
                owner=profile,
                username=profile.user.name,
                email=profile.user.email,
                text='Address updated by owner'
            )
            e.save()
            messages.success(request, 'Address updated successfully')
            # return redirect('owner_details')
        print('\n\nCHECKING UPDATE PROFILE.......')
        if request.POST.get('update_profile'):
            print('UPDATE PROFILE TRUE.......')
            details.name = request.POST.get('name')
            details.contact = request.POST.get('contact')
            cheque_image = request.FILES.get('cheque_image')
            if cheque_image:
                profile.cheque_image = cheque_image
            profile.bank_account_no = request.POST.get('bank_account_no')
            profile.ifsc_code = request.POST.get('ifsc_code')
            profile.account_holders_name = request.POST.get(
                'account_holders_name')
            details.save()
            print(
                f'BA: {profile.bank_account_no} IFS: {profile.ifsc_code} AHN: {profile.account_holders_name}')
            profile.save()
            e = Event(
                owner=profile,
                username=profile.user.name,
                email=profile.user.email,
                text='Profile updated updated by owner'
            )
            e.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('owner_details')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        addrform = owner_address_form(instance=profile)
        data = {'profile': profile, 'details': details, 'vendor': vendor,
                'addrform': addrform, 'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "owner_details.html", data)
    else:
        return redirect('login_page')


def owner_driver_details(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        driver = DriverProfile.objects.filter(owner=owner).first()
        if driver:
            drform = driver_form(instance=driver)
            update = True
        else:
            drform = driver_form()
            update = False
        if request.POST.get('location'):
            current_location = request.POST.get('location')
            if driver:
                driver.current_location = current_location
                driver.save()
                e = Event(
                    driver=driver,
                    username=owner.user.name,
                    email=owner.user.email,
                    text='Driver location set to ' + current_location
                )
                e.save()
                return JsonResponse({'success': True})
        if request.POST.get('name'):
            if not driver:
                driver = DriverProfile()
                driver.owner = owner
            driver.name = request.POST.get('name')
            driver.phone = request.POST.get('phone')
            picture = request.FILES.get('picture')
            if picture:
                driver.picture = picture
            aadhar_card_number = request.POST.get('aadhar_card_number')
            if aadhar_card_number:
                driver.aadhar_card_number = aadhar_card_number
            aadhar_front_image = request.FILES.get('aadhar_front_image')
            if aadhar_front_image:
                driver.aadhar_front_image = aadhar_front_image
            aadhar_back_image = request.FILES.get('aadhar_front_image')
            if aadhar_back_image:
                driver.aadhar_back_image = aadhar_back_image
            driving_licence_front = request.FILES.get('driving_licence_front')
            if driving_licence_front:
                driver.driving_licence_front = driving_licence_front
            driving_licence_back = request.FILES.get('driving_licence_back')
            if driving_licence_back:
                driver.driving_licence_back = driving_licence_back
            police_verification = request.FILES.get('police_verification')
            if police_verification:
                driver.police_verification = police_verification
            driving_licence_number = request.POST.get('driving_licence_number')
            if driving_licence_number:
                driver.driving_licence_number = driving_licence_number
            driving_licence_expiry_date = request.POST.get(
                'driving_licence_expiry_date')
            if driving_licence_expiry_date:
                driver.driving_licence_expiry_date = driving_licence_expiry_date
            taxi_badge_number = request.POST.get('taxi_badge_number')
            if taxi_badge_number:
                driver.taxi_badge_number = taxi_badge_number
            driver.save()

            if update:
                messages.success(request, 'Profile Updated Successfully')
                e = Event(
                    driver=driver,
                    username=owner.user.name,
                    email=owner.user.email,
                    text='Driver profile updated by owner'
                )
                e.save()
            else:
                messages.success(request, 'Profile Created Successfully')
                e = Event(
                    driver=driver,
                    username=owner.user.name,
                    email=owner.user.email,
                    text='Driver profile created by owner'
                )
                e.save()
            return redirect('owner_driver_details')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'drform': drform, "owner": True, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "owner_driver_details.html", data)
    else:
        return redirect('login_page')


def owner_dashboard(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        car = Car.objects.filter(owner=owner).first()
        driver = DriverProfile.objects.filter(owner=owner).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_vendor:
            return redirect('vendor_dashboard')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {car: 'car', 'driver': driver, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "owner_dashboard.html", data)
    else:
        return redirect('login_page')


def owner_request_trip(request):
	print(f'POST: {request.POST}\nFILES: {request.FILES}')
	if request.user.is_authenticated:
		return render(request, "owner_request_trip.html")
	else:
		return redirect('login_page')

def owner_request_location(request):
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		curr_loc = request.POST.get('curr_loc')
		print(curr_loc, "location address")
		curr_loc_coords = curr_loc.split(',')
		driver = DriverProfile.objects.filter(owner = OwnerProfile.objects.filter(user=details).first())
		print(curr_loc_coords)
		curr_loc_coords.reverse()
		home_location = request.POST.get('home_loc')
		home_loc_coords = home_location.split(',')
		home_loc_coords.reverse()
		driver.request_location = get_location_address(curr_loc_coords)
		driver.request_loc_coords = curr_loc
		driver.has_requested = True
		driver.home_loc_coords = home_loc_coords
		driver.home_location = get_location_address(home_loc_coords)
		data = {}
		notification_text = "Driver " + driver.name + "has requested for a trip from location" + driver.request_location + "to location " + driver.home_location # TODO: driver drop location 
		user = User.objects.filter(is_superuser = True).first()
		payload['head'] = "New Trip"
		payload['body'] = notification_text
		send_user_notification(user=user, payload=payload, ttl=86400)
		return render(request, "owner_request_trip.html", data)
	else:
		return redirect('login_page')

def owner_car(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_vendor:
            return redirect('vendor_dashboard')
        car = Car.objects.filter(owner=owner).first()
        if car:
            update = True
            carform = car_form(instance=car)
        else:
            update = False
            carform = car_form()
        if request.POST:
            if not update:
                car = Car(owner=owner)
            car.type_id = request.POST.get('type')
            car.company_id = request.POST.get('company')
            car.name = request.POST.get('name')
            car.licence_plate_no = request.POST.get('licence_plate_no')
            rc_book_front = request.FILES.get('rc_book_front')
            if rc_book_front:
                car.rc_book_front = rc_book_front
            rc_book_back = request.FILES.get('rc_book_back')
            if rc_book_back:
                car.rc_book_back = rc_book_back
            rc_book_expiry_date = request.POST.get('rc_book_expiry_date')
            if rc_book_expiry_date:
                car.rc_book_expiry_date = rc_book_expiry_date
            car_year = request.POST.get('car_year')
            if car_year:
                car.car_year = car_year
            owner_name = request.POST.get('owner_name')
            if owner_name:
                car.owner_name = owner_name
            chassi_number = request.POST.get('chassi_number')
            if chassi_number:
                car.chassi_number = chassi_number
            insurance_no = request.POST.get('insurance_no')
            if insurance_no:
                car.insurance_no = insurance_no
            insurance_picture = request.FILES.get('insurance_picture')
            if insurance_picture:
                car.insurance_picture = insurance_picture
            insurance_expiry_date = request.POST.get('insurance_expiry_date')
            if insurance_expiry_date:
                car.insurance_expiry_date = insurance_expiry_date
            insurance_company = request.POST.get('insurance_company')
            if insurance_company:
                car.insurance_company = insurance_company
            fitness_certificate = request.FILES.get('fitness_certificate')
            if fitness_certificate:
                car.fitness_certificate = fitness_certificate
            fitness_expiry_date = request.POST.get('fitness_expiry_date')
            if fitness_expiry_date:
                car.fitness_expiry_date = fitness_expiry_date
            car_front = request.FILES.get('car_front')
            if car_front:
                car.car_front = car_front
            car_back = request.FILES.get('car_back')
            if car_back:
                car.car_back = car_back
            car_side_left = request.FILES.get('car_side_left')
            if car_side_left:
                car.car_side_left = car_side_left
            car_side_right = request.FILES.get('car_side_right')
            if car_side_right:
                car.car_side_right = car_side_right
            car_interior_front = request.FILES.get('car_interior_front')
            if car_interior_front:
                car.car_interior_front = car_interior_front
            car_interior_back = request.FILES.get('car_interior_back')
            if car_interior_back:
                car.car_interior_back = car_interior_back
            car_dickie = request.FILES.get('car_dickie')
            if car_dickie:
                car.car_dickie = car_dickie
            car.save()
            if update:
                e = Event(
                    car=car,
                    username=owner.user.name,
                    email=owner.user.email,
                    text='Car details updated by owner'
                )
                e.save()
                messages.success(request, 'Car Edited Successfully')
            else:
                e = Event(
                    car=car,
                    username=owner.user.name,
                    email=owner.user.email,
                    text='Car details added by owner'
                )
                e.save()
                messages.success(request, 'Car Added Successfully')
            return redirect('owner_car')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'carform': carform, 'owner': True, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "vendor_add_car.html", data)
    else:
        return redirect('login_page')


def owner_home(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_vendor:
            return redirect('vendor_dashboard')
        owner_driver = owner.drivers.filter(is_verified=True).first()
        owner_car = owner.cars.filter(is_verified=True).first()
        if not owner_driver or not owner_car or not owner.is_active:
            verified = False
        else:
            verified = True
        all = False
        if request.POST.get('reject'):
            trip_id = request.POST.get('reject')
            trip = Trip.objects.get(pk=trip_id)
            trip.rejected_by.add(owner)
            trip.save()
            e = Event(
                trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Trip rejected by ' + owner.user.name
            )
            e.save()
            messages.success(request, 'Trip removed')
            return redirect('owner_home')
        if request.POST.get('accept'):
            trip_id = request.POST.get('accept')
            trip = Trip.objects.get(pk=trip_id)
            trip.owner = owner
            trip.driver = owner_driver
            trip.car = owner_car
            if not trip.start_otp:
                trip.generate_otp()
            trip.save()
            e = Event(
                trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Trip accepted by ' + owner.user.name
            )
            e.save()
            messages.success(request, 'Trip Accepted Successfully')
            return redirect('owner_home')
        if request.POST.get('acceptowner'):
            trip_id = request.POST.get('acceptowner')
            trip = VendorTrip.objects.get(pk=trip_id)
            if trip.is_demo:
                messages.error(
                    request, 'This booking was already accepted by other driver or vendor')
                return redirect('owner_home')
            trip.owner = owner
            trip.driver = owner_driver
            trip.car = owner_car
            trip.save()
            if not trip.start_otp:
                trip.generate_otp()
            e = Event(
                vendor_trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Trip accepted by ' + owner.user.name + ', driver: ' +
                owner_driver.name + ', car : ' + owner_car.licence_plate_no
            )
            e.save()
            messages.success(request, 'Trip added to acccepted trips')
            return redirect('owner_home')
        if request.POST.get('rejectowner'):
            trip_id = request.POST.get('rejectowner')
            trip = VendorTrip.objects.get(pk=trip_id)
            trip.rejected_by.add(owner)
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Trip rejected by ' + owner.user.name
            )
            e.save()
            messages.success(request, 'Trip removed')
            return redirect('owner_home')
        if request.POST.get('update_states'):
            states_id = request.POST.getlist('states')
            if not states_id:
                owner.states.clear()
            else:
                owner.states.clear()
                owner.states.add(*states_id)
            messages.success(request, 'States updated successfully')
            return redirect('owner_home')
        rejected_trips = owner.rejected_trips.all()
        rejected_vendor_trips = owner.rejected_vendor_trips.all()
        vendor_trips = VendorTrip.objects.filter(
            is_verified=True,
            is_complete=False,
            owner__isnull=True,
            is_canceled=False,
        ).order_by('-pickup_date')
        vendor_trips = vendor_trips.exclude(poster=owner)
        vendor_trips = vendor_trips.exclude(id__in=rejected_vendor_trips)
        trips = Trip.objects.filter(
            is_verified=True,
            is_complete=False,
            owner__isnull=True,
            is_canceled=False,
        ).order_by('-pickup_date')
        temp_trips = Trip.objects.filter(is_verified=True)
        trips = trips.exclude(id__in=rejected_trips)
        print(f'TRIPS: {trips}, TRIPS: {temp_trips}')
        owner_states = []
        for state in owner.states.all():
            owner_states.append(state.name)
        filtered_trips = []
        print(f'Owner States: {owner_states}')
        for trip in trips:
            print(
                f'Trip Pickup: #{trip.pickup_state}# Trip Drop: #{trip.drop_state}#')
            if trip.pickup_state in owner_states or trip.drop_state in owner_states:
                filtered_trips.append([trip, True])
        for trip in vendor_trips:
            if trip.pickup_state in owner_states or trip.drop_state in owner_states:
                filtered_trips.append([trip, False])
        trips = filtered_trips
        print(f'FILTERED_TRIPS: {filtered_trips}')
        sform = owner_state_form(instance=owner)
        print(f'TRIPS', trips)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'trips': trips, 'state_form': sform, 'verified': verified,
                'details': details, 'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "owner_home.html", data)
    else:
        return redirect('login_page')


def owner_my_trips(request):
	print(f'POST: {request.POST}\nFILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		customer = CustomerProfile.objects.filter(user=details).first()
		if customer:
			return redirect('customer_dashboard')
		if owner.is_vendor:
			return redirect('vendor_dashboard')
		if request.POST.get('markcomplete'):
			trip_id = request.POST.get('markcomplete')
			trip = Trip.objects.get(pk=trip_id)
			trip.driver.has_requested = False
			trip.is_complete = True
			trip.save()
			print(trip.driver.has_requested)
			print(trip.id)
			e = Event(
				trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip marked complete by ' + owner.user.name
			)
			e.save()
			messages.success(request, 'Trip updated successfully')
			return redirect('owner_my_trips')
		if request.POST.get('markcompletevendor'):
			trip_id = request.POST.get('markcompletevendor')
			trip = VendorTrip.objects.get(pk=trip_id)
			trip.driver.has_requested = False
			trip.is_complete = True
			trip.save()
			print(trip.id)
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip marked complete by ' + owner.user.name
			)
			e.save()
			messages.success(request, 'Trip updated successfully')
			return redirect('owner_my_trips')
		owner_driver = owner.drivers.filter(is_verified=True).first()
		owner_car = owner.cars.filter(is_verified=True).first()
		trips = owner.trips.all().order_by('-pickup_date')
		vendor_trips = owner.vendor_trips.all().order_by('-pickup_date')
		temp_trips = []
		for trip in trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
			temp_trips.append([trip, True, show_complete])
		for trip in vendor_trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
			temp_trips.append([trip, False, show_complete])
		trips = temp_trips
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		data={'trips':trips, 'details':details , 'notify':unseen_notifications, 'unseen_count': unseen_count}
		return render(request, "owner_my_trips.html", data)
	else:
		return redirect('login_page')

def owner_active_trips(request):
	print(f'POST: {request.POST}\nFILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		customer = CustomerProfile.objects.filter(user=details).first()
		if customer:
			return redirect('customer_dashboard')
		if owner.is_vendor:
			return redirect('vendor_dashboard')
		if request.POST.get('startvendor'):
			trip_id = request.POST.get('startvendor')
			trip = VendorTrip.objects.get(pk=trip_id)
			trip.is_started = True
			trip.save()
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip started by ' + owner.user.name 
			)
			e.save()
			messages.success(request, 'Trip started successfully')
			return redirect('owner_active_bookings')
		if request.POST.get('start'):
			trip_id = request.POST.get('start')
			trip = Trip.objects.get(pk=trip_id)
			start_otp = request.POST.get('start_otp')
			if start_otp == trip.start_otp:
				trip.is_started = True
				trip.save()
				payment_detail = trip.payment_detail.first()
				if not payment_detail:
					trip.generate_payment_detail_advance()
				e = Event(
					trip = trip,
					username = owner.user.name,
					email = owner.user.email,
					text = 'Trip started by ' + owner.user.name 
				)
				e.save()
				messages.success(request, 'Trip started successfully')
			else:
				messages.error(request, 'Incorrect OTP')
			return redirect('owner_active_bookings')
		if request.POST.get('markcomplete'):
			trip_id = request.POST.get('markcomplete')
			trip = Trip.objects.get(pk=trip_id)
			trip.driver.has_requested = False
			end_otp = request.POST.get('end_otp')
			if trip.end_otp == end_otp:
				total_distance = request.POST.get('total_distance')
				payment_detail = trip.payment_detail.first()
				customer_wallet = trip.customer.wallet.first()
				customer_wallet.customer_to_vendor_payment(payment_detail)
				trip.is_complete = True
				trip.save()
				e = Event(
					trip = trip,
					username = owner.user.name,
					email = owner.user.email,
					text = 'Trip marked complete by ' + owner.user.name 
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
			else:
				messages.error(request, 'Incorrect OTP')
			return redirect('owner_active_bookings')
		if request.POST.get('markcompletevendor'):
			trip_id = request.POST.get('markcomplete')
			trip = VendorTrip.objects.get(pk=trip_id)
			trip.is_complete = True
			trip.save()
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip marked complete by ' + owner.user.name 
			)
			e.save()
			messages.success(request, 'Trip completed successfully')
			return redirect('owner_active_bookings')
		trips = owner.trips.filter(is_complete=False, is_verified=True).order_by('-pickup_date')
		vendor_trips = owner.vendor_trips.filter(is_complete=False, is_verified=True).order_by('-pickup_date')
		temp = []
		for trip in trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
				print(trip.id)
			show_start = False
			pickup_time = datetime.datetime.combine(trip.pickup_date, trip.pickup_time)
			if (datetime.datetime.now() > pickup_time) and not trip.is_started:
				show_start = True
			print(f'TRIP: {trip} \nPICKUP_TIME: {pickup_time} \nNOW: {datetime.datetime.now()} \nSHOW_START: {show_start} \nDROP_TIME: {drop_time} \nSHOW_COMPLETE: {show_complete}')
			temp.append([trip,True, show_complete, show_start])
		for trip in vendor_trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
				print(trip.id)
			show_start = False
			pickup_time = datetime.datetime.combine(trip.pickup_date, trip.pickup_time)
			if (datetime.datetime.now() > pickup_time) and not trip.is_started:
				show_start = True
			print(f'TRIP: {trip} \nPICKUP_TIME: {pickup_time} \nNOW: {datetime.datetime.now()} \nSHOW_START: {show_start} \nDROP_TIME: {drop_time} \nSHOW_COMPLETE: {show_complete}')
			temp.append([trip,False, show_complete, show_start])
		trips = temp
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		data={'trips':trips, 'active_bookings': True, 'details':details, 'notify':unseen_notifications, 'unseen_count': unseen_count}
		print(f'DATA: {data}')
		return render(request, "owner_active_bookings.html", data)
	else:
		return redirect('login_page')

def owner_post_trip(request):
	print(f'THIS IS POST: {request.POST}')
	print(f'THIS IS GET: {request.GET}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		if profile:
			return redirect('customer_dashboard')
		if not owner.is_active:
			messages.error(request, 'Sorry! Please contact customer care to activate your account.')
			return redirect('dashboard')
		# Confirm Booking 
		if request.POST.get('confirm_without_traveller'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('car_type')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			days = request.GET.get('days')
			vendor_amount = request.GET.get('vendor_amount')
			if days == 'None':
				days = 0
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('owner_post_trip')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			total_time = time + 2.0
			pickup_temp_date = datetime.datetime.strptime(pickup_date, '%Y-%m-%d')
			pickup_temp_time = datetime.datetime.strptime(pickup_time, '%H:%M').time()
			pickup_datetime = datetime.datetime.combine(pickup_temp_date, pickup_temp_time)
			drop_datetime = pickup_datetime + datetime.timedelta(days=int(days), hours=total_time)
			print(f'ptd: {pickup_temp_date} ptt: {pickup_temp_time} pdatetime: {pickup_datetime} drop_datetime: {drop_datetime}')
			car_type = CarType.objects.get(pk=car_type_id)
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			# New Trip generation
			trip = VendorTrip()
			trip.pickup_city = pickup_city
			trip.pickup_state = pickup_state
			trip.drop_city = drop_city
			trip.drop_state = drop_state
			trip.customer = profile
			trip.pickup_date = pickup_date
			trip.pickup_time = pickup_time
			trip.drop_time = drop_datetime
			trip.car_type = car_type
			print(f'PICKUP CORDS: {pickup_cordinates} DROP CORDS: {drop_cordinates}')
			trip.pickup_location = pickup_cordinates
			trip.drop_location = drop_cordinates
			trip.pickup_address = pickup_address
			trip.drop_address = drop_address
			if trip_type == 'round':
				trip.round_trip = True
				trip.days = days
			trip.vendor_amount = vendor_amount
			trip.distance = distance
			trip.poster = owner
			trip.is_verified = True
			trip.save()
			tdate = trip.pickup_date
			tdate = tdate.replace('-','')	
			ttime = trip.pickup_time
			ttime = ttime.replace(':','')
			trip_no_str = tdate + ttime + '000000'
			trip_no_str = str(int(trip_no_str) + int(trip.id))
			trip.trip_no = trip_no_str
			trip.save()
			print(f'AFTER SAVE PICKUP CORDS: {trip.pickup_location} DROP CORDS: {trip.drop_location}')
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip created by ' + owner.user.name 
			)
			e.save()
			return redirect('owner_posted_trips')
		if request.POST.get('confirm_booking'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('car_type')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			days = request.GET.get('days')
			vendor_amount = request.GET.get('vendor_amount')
			if days == 'None':
				days = 0
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('owner_post_trip')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()

			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			total_time = time + 2.0
			pickup_temp_date = datetime.datetime.strptime(pickup_date, '%Y-%m-%d')
			pickup_temp_time = datetime.datetime.strptime(pickup_time, '%H:%M').time()
			pickup_datetime = datetime.datetime.combine(pickup_temp_date, pickup_temp_time)
			drop_datetime = pickup_datetime + datetime.timedelta(days=int(days), hours=total_time)
			print(f'ptd: {pickup_temp_date} ptt: {pickup_temp_time} pdatetime: {pickup_datetime} drop_datetime: {drop_datetime}')
			car_type = CarType.objects.get(pk=car_type_id)
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			# New Trip generation
			trip = VendorTrip()
			trip.pickup_city = pickup_city
			trip.pickup_state = pickup_state
			trip.drop_city = drop_city
			trip.drop_state = drop_state
			trip.customer = profile
			trip.pickup_date = pickup_date
			trip.pickup_time = pickup_time
			trip.drop_time = drop_datetime
			trip.car_type = car_type
			print(f'PICKUP CORDS: {pickup_cordinates} DROP CORDS: {drop_cordinates}')
			trip.pickup_location = pickup_cordinates
			trip.drop_location = drop_cordinates
			trip.pickup_address = pickup_address
			trip.drop_address = drop_address
			if trip_type == 'round':
				trip.round_trip = True
				trip.days = days
			trip.vendor_amount = vendor_amount
			trip.distance = distance
			trip.poster = owner
			trip.is_verified = True
			trip.save()
			tdate = trip.pickup_date
			tdate = tdate.replace('-','')	
			ttime = trip.pickup_time
			ttime = ttime.replace(':','')
			trip_no_str = tdate + ttime + '000000'
			trip_no_str = str(int(trip_no_str) + int(trip.id))
			trip.trip_no = trip_no_str
			trip.save()
			print(f'AFTER SAVE PICKUP CORDS: {trip.pickup_location} DROP CORDS: {trip.drop_location}')
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip created by ' + owner.user.name 
			)
			e.save()
			# Travellers Object
			traveller = TravellersInformation()
			traveller.vendor_trip = trip
			traveller.name = request.POST.get('name')
			traveller.phone = request.POST.get('phone')
			traveller.email = request.POST.get('email')
			traveller.address = request.POST.get('address')
			traveller.no_of_travellers = request.POST.get('no_of_travellers')
			traveller.no_of_bags = request.POST.get('no_of_bags')
			traveller.special_instructions = request.POST.get('special_instructions')
			carrier = False
			if request.POST.get('carrier_required') == 'on':
				carrier = True
			traveller.carrier_required = carrier
			traveller.save()
			return redirect('owner_posted_trips')
		# Pick up location
		if request.GET.get('pickup_location'):
			pickup_location = request.GET.get('pickup_location')
			trip_type = request.GET.get('trip_type')
			days = request.GET.get('days')
			drop_location = request.GET.get('drop_location')
			trip_perimeter = request.GET.get('trip_perimeter')

			if not drop_location:
				tform = trip_drop(initial={'pickup_location':pickup_location})
				data = {'tform':tform,'trip_type':trip_type, 'days':days, 'trip_perimeter': trip_perimeter}
				return render(request, 'owner_post_trip.html', data)
		# Drop Location
		if request.GET.get('drop_location'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type = request.GET.get('car_type')
			trip_type = request.GET.get('trip_type')
			days = request.GET.get('days')
			if not car_type:
				if not(pickup_location and drop_location):
					messages.error(request, 'Please enter valid details')
					return redirect('owner_post_trip')
				pickup_cordinates = pickup_location.split(',')
				drop_cordinates = drop_location.split(',')
				pickup_cordinates.reverse()
				drop_cordinates.reverse()
				distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
				if not distance:
					messages.error(request, 'Please select valid locations')
					return redirect('owner_post_trip')
				car_types = CarType.objects.filter(is_active=True)
				pickup_address = get_location_address(pickup_cordinates)
				drop_address = get_location_address(drop_cordinates)
				data = {
					'pickup_address':pickup_address,
					'drop_address':drop_address, 
					'car_types': car_types, 
					'pickup_location': pickup_location, 
					'drop_location': drop_location,
					'trip_type': trip_type,
					'days': days,
					'details':details
					}
				return render(request, 'owner_select_cars.html', data)
		# Select time and car type
		if request.GET.get('car_type'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('car_type')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			vendor_amount = request.GET.get('vendor_amount')
			days = request.GET.get('days')
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('owner_post_trip')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			car_type = CarType.objects.get(pk=car_type_id)
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			trform = traveller_form()
			data = {
				'vendor_amount':vendor_amount,
				'pickup_address':pickup_address,
				'drop_address':drop_address, 
				'pickup_location':pickup_location, 
				'pickup_time': pickup_time,
				'pickup_date': pickup_date,
				'drop_location':drop_location, 
				'trform': trform, 
				'distance': distance,
				'trip_type': trip_type,
				'days': days,
				'car_type':car_type,
				'distance': round(distance, 2), 
				'details':details
				}
			return render(request, 'owner_confirm_booking.html', data)
		tform = trip_pickup()
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		data = {'tform':tform, 'notify':unseen_notifications, 'unseen_count': unseen_count}
		return render(request, 'owner_post_trip.html', data)
	else:
		return redirect('login_page')

def owner_posted_trips(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_vendor:
            return redirect('vendor_details')
        if request.POST.get('makevisible'):
            trip_id = request.POST.get('makevisible')
            trip = VendorTrip.objects.get(pk=trip_id)
            trip.acceptor_is_visible = True
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Traveller details made visible by ' + owner.user.name
            )
            e.save()
            messages.success(
                request, 'Traveller details made visible successfully')
            return redirect('owner_posted_trips')
        if request.POST.get('hidedetails'):
            trip_id = request.POST.get('hidedetails')
            trip = VendorTrip.objects.get(pk=trip_id)
            trip.acceptor_is_visible = False
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Traveller details made hidden by ' + owner.user.name
            )
            e.save()
            messages.success(
                request, 'Traveller details made hidden successfully')
            return redirect('owner_posted_trips')
        trips = owner.posted_trips.all().order_by('-pickup_date')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'trips': trips, 'posted_trips': True, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        print(f'DATA: {data}')
        return render(request, "owner_posted_trips.html", data)
    else:
        return redirect('login_page')


def owner_posted_trip_view(request, trip_id):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_vendor:
            return redirect('vendor_details')
        profile = owner
        all_trips = owner.posted_trips.all()
        this_trip = VendorTrip.objects.filter(pk=trip_id).first()
        print(f'ALL: {all_trips}\n VENDOR: {this_trip}')
        if not this_trip:
            return redirect('owner_posted_trips')
        if this_trip in all_trips:
            trip_type = 'round' if this_trip.round_trip else 'oneway'
            distance = this_trip.distance
            days = this_trip.days
            if request.POST.get('vendor_amount'):
                this_trip.vendor_amount = int(
                    request.POST.get('vendor_amount'))
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Vendor amount updated by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Trip cancelled successfully')
                return redirect('vendor_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('delete'):
                this_trip.delete()
                messages.success(request, 'Trip deleted successfully')
                return redirect('owner_posted_trips')
            if request.POST.get('cancel'):
                this_trip.is_canceled = True
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Trip cancelled by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Trip cancelled successfully')
                return redirect('owner_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('time'):
                this_trip.pickup_time = request.POST.get('time')
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Trip details updated by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Pickup time updated successfully')
                return redirect('owner_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('date'):
                this_trip.pickup_date = request.POST.get('date')
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Trip details updated by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Pickup date updated successfully')
                return redirect('owner_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('car_type'):
                car_type_id = request.POST.get('car_type')
                car_type = CarType.objects.get(pk=car_type_id)
                this_trip.car_type = car_type
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Trip details updated by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Car type updated successfully')
                return redirect('owner_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('traveller_edit'):
                tinfo = this_trip.traveller.first()
                if tinfo:
                    trform = traveller_form(request.POST, instance=tinfo)
                else:
                    trform = traveller_form(request.POST)
                if trform.is_valid():
                    tr_instance = trform.save()
                    tr_instance.vendor_trip = this_trip
                    tr_instance.save()
                    e = Event(
                        vendor_trip=this_trip,
                        username=profile.user.name,
                        email=profile.user.email,
                        text='Traveller details updated by ' + profile.user.name
                    )
                    e.save()
                else:
                    print(f'ERRROR: {trform.errors}')
                    messages.error(request, 'Error: Please enter valid data')
                    return redirect('owner_posted_trip_view', trip_id=this_trip.id)
                messages.success(
                    request, 'Traveller information updated successfully')
                return redirect('owner_posted_trip_view', trip_id=this_trip.id)
            car_types = CarType.objects.filter(is_active=True)
            tinfo = this_trip.traveller.first()
            if tinfo:
                trform = traveller_form(instance=tinfo)
            else:
                trform = traveller_form()
            unseen_notifications = list(
                details.notifications.filter(seen=False).order_by('-date'))
            all_notifications = list(
                details.notifications.all().order_by('-date'))
            unseen_count = len(unseen_notifications)
            if len(all_notifications) > 5:
                while len(unseen_notifications) < 5:
                    unseen_notifications.append(all_notifications.pop(0))
            else:
                unseen_notifications + all_notifications
            data = {'trip': this_trip, 'car_types': car_types, 'trform': trform,
                    'details': details, 'notify': unseen_notifications, 'unseen_count': unseen_count}
            return render(request, 'owner_poster_trip_view.html', data)
        else:
            return redirect('vendor_active_bookings')
    else:
        return redirect('login_page')


def owner_edit_pickup(request, trip_id):
    print(f'POST: {request.POST}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_vendor:
            return redirect('vendor_details')
        profile = owner
        trip = VendorTrip.objects.get(pk=trip_id)
        if request.POST.get('pickup_location'):
            pickup_location = request.POST.get('pickup_location')
            pickup_cordinates = pickup_location.split(',')
            pickup_cordinates.reverse()
            drop_cordinates = trip.drop_location
            pickup_address = get_location_address(pickup_cordinates)
            if pickup_address == 'Invalid Address':
                messages.error(request, 'Please Select Valid Address')
                return redirect('owner_posted_trip_view', trip_id=trip.id)
            distance, time = get_distance_and_time(
                pickup_cordinates, drop_cordinates)
            # Saving Updated Data
            trip.pickup_location = pickup_cordinates
            trip.pickup_address = pickup_address
            trip.distance = distance
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=profile.user.name,
                email=profile.user.email,
                text='Pickup location updated by ' + profile.user.name
            )
            e.save()
            return redirect('owner_posted_trip_view', trip_id=trip.id)
        tform = trip_pickup(instance=trip)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'tform': tform, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, 'owner_edit_location.html', data)
    else:
        return redirect('login_page')


def owner_edit_drop(request, trip_id):
    print(f'POST: {request.POST}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_vendor:
            return redirect('vendor_details')
        profile = owner
        trip = VendorTrip.objects.get(pk=trip_id)
        if request.POST.get('drop_location'):
            drop_location = request.POST.get('drop_location')
            drop_cordinates = drop_location.split(',')
            drop_cordinates.reverse()
            pickup_cordinates = trip.pickup_location
            drop_address = get_location_address(drop_cordinates)
            if drop_address == 'Invalid Address':
                messages.error(request, 'Please Select Valid Address')
                return redirect('owner_posted_trip_view', trip_id=trip.id)
            distance, time = get_distance_and_time(
                pickup_cordinates, drop_cordinates)

            # Saving Updated Data
            trip.drop_location = drop_cordinates
            trip.drop_address = drop_address
            trip.distance = distance
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=profile.user.name,
                email=profile.user.email,
                text='Drop location updated by ' + profile.user.name
            )
            e.save()
            return redirect('owner_posted_trip_view', trip_id=trip.id)
        tform = trip_drop(instance=trip)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'tform': tform, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, 'owner_edit_location.html', data)
    else:
        return redirect('login_page')


def owner_completed_bookings(request):
	print(f'POST: {request.POST}\nFILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		customer = CustomerProfile.objects.filter(user=details).first()
		if customer:
			return redirect('customer_dashboard')
		if owner.is_vendor:
			return redirect('vendor_dashboard')
		owner_driver = owner.drivers.filter(is_verified=True).first()
		owner_car = owner.cars.filter(is_verified=True).first()
		trips = owner.trips.filter(is_complete=True).order_by('-pickup_date')
		vendor_trips = owner.vendor_trips.filter(is_complete=True).order_by('-pickup_date')
		temp_trips = []
		for trip in trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
			temp_trips.append([trip, True, show_complete])
		for trip in vendor_trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
			temp_trips.append([trip, False, show_complete])
		trips = temp_trips
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		data={'trips':trips, 'completed_booking':True, 'details':details, 'notify':unseen_notifications, 'unseen_count': unseen_count}
		return render(request, "owner_my_trips.html", data)
	else:
		return redirect('login_page')

def vendor_home(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_details')
        owner_driver = owner.drivers.filter(is_verified=True).first()
        owner_car = owner.cars.filter(is_verified=True).first()
        if not owner_driver or not owner_car or not owner.is_verified:
            verified = False
        else:
            verified = True
        if request.POST.get('update_states'):
            states_id = request.POST.getlist('states')
            if not states_id:
                owner.states.clear()
            else:
                owner.states.clear()
                owner.states.add(*states_id)
            messages.success(request, 'States updated successfully')
            return redirect('vendor_home')
        if request.POST.get('reject'):
            trip_id = request.POST.get('reject')
            trip = Trip.objects.get(pk=trip_id)
            trip.rejected_by.add(owner)
            trip.save()
            e = Event(
                trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Trip rejected by ' + owner.user.name
            )
            e.save()
            messages.success(request, 'Trip removed')
            return redirect('vendor_home')
        if request.POST.get('accept'):
            trip_id = request.POST.get('accept')
            car_id = request.POST.get('car')
            driver_id = request.POST.get('driver')
            trip = Trip.objects.get(pk=trip_id)
            car = Car.objects.get(pk=car_id)
            driver = DriverProfile.objects.get(pk=driver_id)
            trip.owner = owner
            trip.driver = driver
            trip.car = car
            if not trip.start_otp:
                trip.generate_otp()
            trip.save()
            e = Event(
                trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Trip accepted by ' + owner.user.name + ', driver: ' +
                driver.name + ', car : ' + car.licence_plate_no
            )
            e.save()
            messages.success(request, 'Trip added to acccepted trips')
            return redirect('vendor_active_bookings')
        if request.POST.get('acceptvendor'):
            trip_id = request.POST.get('acceptvendor')
            car_id = request.POST.get('car')
            driver_id = request.POST.get('driver')
            trip = VendorTrip.objects.get(pk=trip_id)
            if trip.is_demo:
                messages.error(
                    request, 'This booking was already accepted by other driver or vendor')
                return redirect('vendor_home')
            car = Car.objects.get(pk=car_id)
            driver = DriverProfile.objects.get(pk=driver_id)
            trip.owner = owner
            trip.driver = driver
            trip.car = car
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Trip accepted by ' + owner.user.name + ', driver: ' +
                driver.name + ', car : ' + car.licence_plate_no
            )
            e.save()
            messages.success(request, 'Trip added to acccepted trips')
            return redirect('vendor_active_bookings')
        if request.POST.get('rejectowner'):
            trip_id = request.POST.get('rejectowner')
            trip = VendorTrip.objects.get(pk=trip_id)
            trip.rejected_by.add(owner)
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Trip rejected by ' + owner.user.name
            )
            e.save()
            messages.success(request, 'Trip removed')
            return redirect('vendor_home')
        vendor_drivers = owner.drivers.filter(is_verified=True)
        vendor_cars = owner.cars.filter(is_verified=True)
        rejected_trips = owner.rejected_trips.all()
        rejected_vendor_trips = owner.rejected_vendor_trips.all()
        trips = Trip.objects.filter(
            is_verified=True,
            is_complete=False,
            owner__isnull=True,
            is_canceled=False,
        ).order_by('-pickup_date')
        vendor_trips = VendorTrip.objects.filter(
            is_verified=True,
            is_complete=False,
            owner__isnull=True,
            is_canceled=False,
        ).order_by('-pickup_date')
        vendor_trips = vendor_trips.exclude(poster=owner)
        vendor_trips = vendor_trips.exclude(id__in=rejected_vendor_trips)
        trips = trips.exclude(id__in=rejected_trips)
        owner_states = []
        for state in owner.states.all():
            owner_states.append(state.name)
        filtered_trips = []
        for trip in trips:
            if trip.pickup_state in owner_states or trip.drop_state in owner_states:
                filtered_trips.append([trip, True])
        for trip in vendor_trips:
            if trip.pickup_state in owner_states or trip.drop_state in owner_states:
                filtered_trips.append([trip, False])
        trips = filtered_trips
        sform = owner_state_form(instance=owner)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'trips': trips, 'state_form': sform, 'verified': verified, 'drivers': vendor_drivers,
                'cars': vendor_cars, 'details': details, 'notify': unseen_notifications, 'unseen_count': unseen_count}
        print(f'DATA: {data}')
        return render(request, "vendor_home.html", data)
    else:
        return redirect('login_page')


def vendor_my_trips(request):
	print(f'POST: {request.POST}\nFILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		customer = CustomerProfile.objects.filter(user=details).first()
		if customer:
			return redirect('customer_dashboard')
		if owner.is_owner:
			return redirect('owner_details')
		if request.POST.get('reassign'):
			trip_id = request.POST.get('reassign')
			car_id = request.POST.get('car')
			driver_id = request.POST.get('driver')
			trip = Trip.objects.get(pk=trip_id)
			car = Car.objects.get(pk=car_id)
			driver = DriverProfile.objects.get(pk=driver_id)
			trip.owner = owner
			trip.driver = driver
			trip.car = car
			trip.save()
			e = Event(
				trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip updated by ' + owner.user.name + ', driver: ' + driver.name + ', car : ' + car.licence_plate_no
			)
			e.save()
			messages.success(request, 'Trip updated successfully')
			return redirect('vendor_active_bookings')
		if request.POST.get('reassignvendortrip'):
			trip_id = request.POST.get('reassignvendortrip')
			car_id = request.POST.get('car')
			driver_id = request.POST.get('driver')
			trip = VendorTrip.objects.get(pk=trip_id)
			car = Car.objects.get(pk=car_id)
			driver = DriverProfile.objects.get(pk=driver_id)
			trip.owner = owner
			trip.driver = driver
			trip.car = car
			trip.save()
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip updated by ' + owner.user.name + ', driver: ' + driver.name + ', car : ' + car.licence_plate_no
			)
			e.save()
			messages.success(request, 'Trip updated successfully')
			return redirect('vendor_active_bookings')
		if request.POST.get('markcomplete'):
			trip_id = request.POST.get('markcomplete')
			trip = Trip.objects.get(pk=trip_id)
			trip.driver.has_requested = False
			trip.is_complete = True
			trip.save()
			print(trip.id)
			e = Event(
				trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip marked complete by ' + owner.user.name
			)
			e.save()
			messages.success(request, 'Trip updated successfully')
			return redirect('vendor_active_bookings')
		if request.POST.get('markcompletevendor'):
			trip_id = request.POST.get('markcompletevendor')
			trip = VendorTrip.objects.get(pk=trip_id)
			trip.is_complete = True
			trip.save()
			print(trip.id)
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip marked complete by ' + owner.user.name
			)
			e.save()
			messages.success(request, 'Trip updated successfully')
			return redirect('vendor_active_bookings')
		vendor_drivers = owner.drivers.filter(is_verified=True)
		vendor_cars = owner.cars.filter(is_verified=True)
		trips = owner.trips.all().order_by('-pickup_date')
		vendor_trips = owner.vendor_trips.all().order_by('-pickup_date')
		temp = []
		for trip in trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
				print(trip.id)
			temp.append([trip,True, show_complete])
		for trip in vendor_trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
			temp.append([trip,False, show_complete])
		trips = temp
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		data={'trips':trips, 'drivers':vendor_drivers, 'cars':vendor_cars, 'details':details, 'notify':unseen_notifications, 'unseen_count': unseen_count}
		print(f'DATA: {data}')
		return render(request, "vendor_my_trips.html", data)
	else:
		return redirect('login_page')

def vendor_active_bookings(request):
	print(f'POST: {request.POST}\nFILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		customer = CustomerProfile.objects.filter(user=details).first()
		if customer:
			return redirect('customer_dashboard')
		if owner.is_owner:
			return redirect('owner_details')
		if request.POST.get('startvendor'):
			trip_id = request.POST.get('startvendor')
			trip = VendorTrip.objects.get(pk=trip_id)
			trip.is_started = True
			trip.save()
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip started by ' + owner.user.name 
			)
			e.save()
			messages.success(request, 'Trip started successfully')
			return redirect('vendor_active_bookings')
		if request.POST.get('start'):
			trip_id = request.POST.get('start')
			trip = Trip.objects.get(pk=trip_id)
			start_otp = request.POST.get('start_otp')
			print(f'ENtered: {start_otp} tripOTP: {trip.start_otp}')
			if trip.start_otp == start_otp:
				trip.is_started = True
				trip.save()
				payment_detail = trip.payment_detail.first()
				if not payment_detail:
					trip.generate_payment_detail_advance()
				payment_detail = trip.payment_detail.first()
				trip.set_vendor_amounts(payment_detail)
				e = Event(
					trip = trip,
					username = owner.user.name,
					email = owner.user.email,
					text = 'Trip started by ' + owner.user.name 
				)
				e.save()
				messages.success(request, 'Trip started successfully')
			else:
				messages.error(request, 'Incorrect OTP')
			return redirect('vendor_active_bookings')
		if request.POST.get('markcomplete'):
			trip_id = request.POST.get('markcomplete')
			trip = Trip.objects.get(pk=trip_id)
			trip.driver.has_requested = False
			end_otp = request.POST.get('end_otp')
			if trip.end_otp == end_otp:
				trip.is_complete = True
				payment_detail = trip.payment_detail.first()
				customer_wallet = trip.customer.wallet.first()
				customer_wallet.customer_to_vendor_payment(payment_detail)
				trip.save()
				e = Event(
					trip = trip,
					username = owner.user.name,
					email = owner.user.email,
					text = 'Trip marked complete by ' + owner.user.name 
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
			else:
				messages.error(request, 'Incorrect OTP')
			return redirect('vendor_active_bookings')
		if request.POST.get('markcompletevendor'):
			trip_id = request.POST.get('markcomplete')
			trip = VendorTrip.objects.get(pk=trip_id)
			trip.is_complete = True
			trip.save()
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip marked complete by ' + owner.user.name 
			)
			e.save()
			messages.success(request, 'Trip completed successfully')
			return redirect('vendor_active_bookings')
		trips = owner.trips.filter(is_complete=False, is_verified=True).order_by('-pickup_date')
		vendor_trips = owner.vendor_trips.filter(is_complete=False, is_verified=True).order_by('-pickup_date')
		temp = []
		for trip in trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
				print(trip.id)
			show_start = False
			pickup_time = datetime.datetime.combine(trip.pickup_date, trip.pickup_time)
			if (datetime.datetime.now() > pickup_time) and not trip.is_started:
				show_start = True
			print(f'TRIP: {trip} \nPICKUP_TIME: {pickup_time} \nNOW: {datetime.datetime.now()} \nSHOW_START: {show_start} \nDROP_TIME: {drop_time} \nSHOW_COMPLETE: {show_complete}')
			temp.append([trip,True, show_complete, show_start])
		for trip in vendor_trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
				print(trip.id)
			show_start = False
			pickup_time = datetime.datetime.combine(trip.pickup_date, trip.pickup_time)
			if (datetime.datetime.now() > pickup_time) and not trip.is_started:
				show_start = True
			print(f'TRIP: {trip} \nPICKUP_TIME: {pickup_time} \nNOW: {datetime.datetime.now()} \nSHOW_START: {show_start} \nDROP_TIME: {drop_time} \nSHOW_COMPLETE: {show_complete}')
			temp.append([trip,False, show_complete, show_start])
		trips = temp
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		data={'trips':trips, 'active_bookings': True, 'details':details, 'notify':unseen_notifications, 'unseen_count': unseen_count}
		print(f'DATA: {data}')
		return render(request, "vendor_active_bookings.html", data)
	else:
		return redirect('login_page')

def vendor_completed_bookings(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_details')
        trips = owner.trips.filter(is_complete=True).order_by('-pickup_date')
        vendor_trips = owner.vendor_trips.filter(
            is_complete=True).order_by('-pickup_date')
        temp = []
        for trip in trips:
            temp.append([trip, True])
        for trip in vendor_trips:
            temp.append([trip, False])
        trips = temp
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'trips': trips, 'completed_booking': True, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        print(f'DATA: {data}')
        return render(request, "vendor_my_trips.html", data)
    else:
        return redirect('login_page')


def vendor_posted_trips(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_details')
        if request.POST.get('makevisible'):
            trip_id = request.POST.get('makevisible')
            trip = VendorTrip.objects.get(pk=trip_id)
            trip.acceptor_is_visible = True
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Traveller details made visible by ' + owner.user.name
            )
            e.save()
            messages.success(
                request, 'Traveller details made visible successfully')
            return redirect('vendor_posted_trips')
        if request.POST.get('hidedetails'):
            trip_id = request.POST.get('hidedetails')
            trip = VendorTrip.objects.get(pk=trip_id)
            trip.acceptor_is_visible = False
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=owner.user.name,
                email=owner.user.email,
                text='Traveller details made hidden by ' + owner.user.name
            )
            e.save()
            messages.success(
                request, 'Traveller details made hidden successfully')
            return redirect('vendor_posted_trips')
        trips = owner.posted_trips.all().order_by('-pickup_date')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'trips': trips, 'posted_trips': True, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        print(f'DATA: {data}')
        return render(request, "vendor_posted_trips.html", data)
    else:
        return redirect('login_page')


def vendor_posted_trip_view(request, trip_id):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_details')
        profile = owner
        all_trips = owner.posted_trips.all()
        this_trip = VendorTrip.objects.filter(pk=trip_id).first()
        print(f'ALL: {all_trips}\n VENDOR: {this_trip}')
        if not this_trip:
            return redirect('vendor_posted_trips')
        if this_trip in all_trips:
            trip_type = 'round' if this_trip.round_trip else 'oneway'
            distance = this_trip.distance
            days = this_trip.days
            if request.POST.get('vendor_amount'):
                this_trip.vendor_amount = int(
                    request.POST.get('vendor_amount'))
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Vendor amount updated by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Trip cancelled successfully')
                return redirect('vendor_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('delete'):
                this_trip.delete()
                messages.success(request, 'Trip deleted successfully')
                return redirect('vendor_posted_trips')
            if request.POST.get('cancel'):
                this_trip.is_canceled = True
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Trip cancelled by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Trip cancelled successfully')
                return redirect('vendor_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('time'):
                this_trip.pickup_time = request.POST.get('time')
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Trip details updated by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Pickup time updated successfully')
                return redirect('vendor_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('date'):
                this_trip.pickup_date = request.POST.get('date')
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Trip details updated by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Pickup date updated successfully')
                return redirect('vendor_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('car_type'):
                car_type_id = request.POST.get('car_type')
                car_type = CarType.objects.get(pk=car_type_id)
                this_trip.car_type = car_type
                this_trip.save()
                e = Event(
                    vendor_trip=this_trip,
                    username=profile.user.name,
                    email=profile.user.email,
                    text='Trip details updated by ' + profile.user.name
                )
                e.save()
                messages.success(request, 'Car type updated successfully')
                return redirect('vendor_posted_trip_view', trip_id=this_trip.id)
            if request.POST.get('traveller_edit'):
                tinfo = this_trip.traveller.first()
                if tinfo:
                    trform = traveller_form(request.POST, instance=tinfo)
                else:
                    trform = traveller_form(request.POST)
                if trform.is_valid():
                    trform.save()
                    e = Event(
                        vendor_trip=this_trip,
                        username=profile.user.name,
                        email=profile.user.email,
                        text='Traveller details updated by ' + profile.user.name
                    )
                    e.save()
                else:
                    print(f'ERRROR: {trform.errors}')
                    messages.error(request, 'Error: Please enter valid data')
                    return redirect('vendor_posted_trip_view', trip_id=this_trip.id)
                messages.success(
                    request, 'Traveller information updated successfully')
                return redirect('vendor_posted_trip_view', trip_id=this_trip.id)
            car_types = CarType.objects.filter(is_active=True)
            tinfo = this_trip.traveller.first()
            if tinfo:
                trform = traveller_form(instance=tinfo)
            else:
                trform = traveller_form()
            unseen_notifications = list(
                details.notifications.filter(seen=False).order_by('-date'))
            all_notifications = list(
                details.notifications.all().order_by('-date'))
            unseen_count = len(unseen_notifications)
            if len(all_notifications) > 5:
                while len(unseen_notifications) < 5:
                    unseen_notifications.append(all_notifications.pop(0))
            else:
                unseen_notifications + all_notifications
            data = {'trip': this_trip, 'car_types': car_types, 'trform': trform, 'posted_trips': True,
                    'details': details, 'notify': unseen_notifications, 'unseen_count': unseen_count}
            return render(request, 'vendor_poster_trip_view.html', data)
        else:
            return redirect('vendor_active_bookings')
    else:
        return redirect('login_page')


def vendor_edit_pickup(request, trip_id):
    print(f'POST: {request.POST}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_details')
        profile = owner
        trip = VendorTrip.objects.get(pk=trip_id)
        if request.POST.get('pickup_location'):
            pickup_location = request.POST.get('pickup_location')
            pickup_cordinates = pickup_location.split(',')
            pickup_cordinates.reverse()
            drop_cordinates = trip.drop_location
            pickup_address = get_location_address(pickup_cordinates)
            if pickup_address == 'Invalid Address':
                messages.error(request, 'Please Select Valid Address')
                return redirect('vendor_posted_trip_view', trip_id=trip.id)
            distance, time = get_distance_and_time(
                pickup_cordinates, drop_cordinates)
            # Saving Updated Data
            trip.pickup_location = pickup_cordinates
            trip.pickup_address = pickup_address
            trip.distance = distance
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=profile.user.name,
                email=profile.user.email,
                text='Pickup location updated by ' + profile.user.name
            )
            e.save()
            return redirect('vendor_posted_trip_view', trip_id=trip.id)
        tform = trip_pickup(instance=trip)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'tform': tform, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, 'vendor_edit_location.html', data)
    else:
        return redirect('login_page')


def vendor_edit_drop(request, trip_id):
    print(f'POST: {request.POST}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_details')
        profile = owner
        trip = VendorTrip.objects.get(pk=trip_id)
        if request.POST.get('drop_location'):
            drop_location = request.POST.get('drop_location')
            drop_cordinates = drop_location.split(',')
            drop_cordinates.reverse()
            pickup_cordinates = trip.pickup_location
            drop_address = get_location_address(drop_cordinates)
            if drop_address == 'Invalid Address':
                messages.error(request, 'Please Select Valid Address')
                return redirect('vendor_posted_trip_view', trip_id=trip.id)
            distance, time = get_distance_and_time(
                pickup_cordinates, drop_cordinates)

            # Saving Updated Data
            trip.drop_location = drop_cordinates
            trip.drop_address = drop_address
            trip.distance = distance
            trip.save()
            e = Event(
                vendor_trip=trip,
                username=profile.user.name,
                email=profile.user.email,
                text='Drop location updated by ' + profile.user.name
            )
            e.save()
            return redirect('vendor_posted_trip_view', trip_id=trip.id)
        tform = trip_drop(instance=trip)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'tform': tform, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, 'vendor_edit_location.html', data)
    else:
        return redirect('login_page')


def vendor_dashboard(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_details')
        drivers = DriverProfile.objects.filter(owner=owner)
        cars = Car.objects.filter(owner=owner)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'drivers': drivers, 'cars': cars, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "vendor_dashboard.html", data)
    else:
        return redirect('login_page')


def vendor_drivers(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_driver_details')
        drivers = DriverProfile.objects.filter(owner=owner)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'drivers': drivers, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "vendor_drivers.html", data)
    else:
        return redirect('login_page')


def vendor_driver_locations(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_driver_details')
        if request.POST.get('update_location'):
            driver_id = request.POST.get('driver_id')
            location = request.POST.get('location')
            driver = DriverProfile.objects.get(pk=driver_id)
            driver.current_location = location
            driver.save()
            return JsonResponse({'success': 'true'})
        drivers = DriverProfile.objects.filter(owner=owner)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'drivers': drivers, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "vendor_driver_locations.html", data)
    else:
        return redirect('login_page')


def vendor_cars(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_details')
        cars = Car.objects.filter(owner=owner)
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'cars': cars, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        # driver = DriverProfile.objects.filter(owner=owner)
        return render(request, "vendor_cars.html", data)
    else:
        return redirect('login_page')


def vendor_add_car(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_car_add')
        carform = car_form()
        if request.POST:
            car = Car()
            car.owner = owner
            car.type_id = request.POST.get('type')
            car.company_id = request.POST.get('company')
            car.name = request.POST.get('name')
            car.licence_plate_no = request.POST.get('licence_plate_no')
            rc_book_front = request.FILES.get('rc_book_front')
            if rc_book_front:
                car.rc_book_front = rc_book_front
            rc_book_back = request.FILES.get('rc_book_back')
            if rc_book_back:
                car.rc_book_back = rc_book_back
            rc_book_expiry_date = request.POST.get('rc_book_expiry_date')
            if rc_book_expiry_date:
                car.rc_book_expiry_date = rc_book_expiry_date
            car_year = request.POST.get('car_year')
            if car_year:
                car.car_year = car_year
            owner_name = request.POST.get('owner_name')
            if owner_name:
                car.owner_name = owner_name
            chassi_number = request.POST.get('chassi_number')
            if chassi_number:
                car.chassi_number = chassi_number
            insurance_no = request.POST.get('insurance_no')
            if insurance_no:
                car.insurance_no = insurance_no
            insurance_picture = request.FILES.get('insurance_picture')
            if insurance_picture:
                car.insurance_picture = insurance_picture
            insurance_expiry_date = request.POST.get('insurance_expiry_date')
            if insurance_expiry_date:
                car.insurance_expiry_date = insurance_expiry_date
            insurance_company = request.POST.get('insurance_company')
            if insurance_company:
                car.insurance_company = insurance_company
            fitness_certificate = request.FILES.get('fitness_certificate')
            if fitness_certificate:
                car.fitness_certificate = fitness_certificate
            fitness_expiry_date = request.POST.get('fitness_expiry_date')
            if fitness_expiry_date:
                car.fitness_expiry_date = fitness_expiry_date
            car_front = request.FILES.get('car_front')
            if car_front:
                car.car_front = car_front
            car_back = request.FILES.get('car_back')
            if car_back:
                car.car_back = car_back
            car_side_left = request.FILES.get('car_side_left')
            if car_side_left:
                car.car_side_left = car_side_left
            car_side_right = request.FILES.get('car_side_right')
            if car_side_right:
                car.car_side_right = car_side_right
            car_interior_front = request.FILES.get('car_interior_front')
            if car_interior_front:
                car.car_interior_front = car_interior_front
            car_interior_back = request.FILES.get('car_interior_back')
            if car_interior_back:
                car.car_interior_back = car_interior_back
            car_dickie = request.FILES.get('car_dickie')
            if car_dickie:
                car.car_dickie = car_dickie
            car.save()
            e = Event(
                car=car,
                username=owner.user.name,
                email=owner.user.email,
                text='Car added by ' + owner.user.name
            )
            e.save()
            messages.success(request, 'Car Added Successfully')
            return redirect('vendor_cars')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'carform': carform, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "vendor_add_car.html", data)
    else:
        return redirect('login_page')


def vendor_edit_car(request, car_id):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_car_add')
        car = Car.objects.get(pk=car_id)
        carform = car_form(instance=car)
        if request.POST:
            car.type_id = request.POST.get('type')
            car.company_id = request.POST.get('company')
            car.name = request.POST.get('name')
            car.licence_plate_no = request.POST.get('licence_plate_no')
            rc_book_front = request.FILES.get('rc_book_front')
            if rc_book_front:
                car.rc_book_front = rc_book_front
            rc_book_back = request.FILES.get('rc_book_back')
            if rc_book_back:
                car.rc_book_back = rc_book_back
            rc_book_expiry_date = request.POST.get('rc_book_expiry_date')
            if rc_book_expiry_date:
                car.rc_book_expiry_date = rc_book_expiry_date
            car_year = request.POST.get('car_year')
            if car_year:
                car.car_year = car_year
            owner_name = request.POST.get('owner_name')
            if owner_name:
                car.owner_name = owner_name
            chassi_number = request.POST.get('chassi_number')
            if chassi_number:
                car.chassi_number = chassi_number
            insurance_no = request.POST.get('insurance_no')
            if insurance_no:
                car.insurance_no = insurance_no
            insurance_picture = request.FILES.get('insurance_picture')
            if insurance_picture:
                car.insurance_picture = insurance_picture
            insurance_expiry_date = request.POST.get('insurance_expiry_date')
            if insurance_expiry_date:
                car.insurance_expiry_date = insurance_expiry_date
            insurance_company = request.POST.get('insurance_company')
            if insurance_company:
                car.insurance_company = insurance_company
            fitness_certificate = request.FILES.get('fitness_certificate')
            if fitness_certificate:
                car.fitness_certificate = fitness_certificate
            fitness_expiry_date = request.POST.get('fitness_expiry_date')
            if fitness_expiry_date:
                car.fitness_expiry_date = fitness_expiry_date
            car_front = request.FILES.get('car_front')
            if car_front:
                car.car_front = car_front
            car_back = request.FILES.get('car_back')
            if car_back:
                car.car_back = car_back
            car_side_left = request.FILES.get('car_side_left')
            if car_side_left:
                car.car_side_left = car_side_left
            car_side_right = request.FILES.get('car_side_right')
            if car_side_right:
                car.car_side_right = car_side_right
            car_interior_front = request.FILES.get('car_interior_front')
            if car_interior_front:
                car.car_interior_front = car_interior_front
            car_interior_back = request.FILES.get('car_interior_back')
            if car_interior_back:
                car.car_interior_back = car_interior_back
            car_dickie = request.FILES.get('car_dickie')
            if car_dickie:
                car.car_dickie = car_dickie
            car.save()
            e = Event(
                car=car,
                username=owner.user.name,
                email=owner.user.email,
                text='Car edited by ' + owner.user.name
            )
            e.save()
            messages.success(request, 'Car Edited Successfully')
            return redirect('vendor_cars')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'carform': carform, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "vendor_add_car.html", data)
    else:
        return redirect('login_page')


def vendor_add_driver(request):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_driver_details')
        drform = driver_form()
        if request.POST:
            driver = DriverProfile()
            driver.owner = owner
            driver.name = request.POST.get('name')
            driver.phone = request.POST.get('phone')
            picture = request.FILES.get('picture')
            if picture:
                driver.picture = picture
            aadhar_card_number = request.POST.get('aadhar_card_number')
            if aadhar_card_number:
                driver.aadhar_card_number = aadhar_card_number
            aadhar_front_image = request.FILES.get('aadhar_front_image')
            if aadhar_front_image:
                driver.aadhar_front_image = aadhar_front_image
            aadhar_back_image = request.FILES.get('aadhar_front_image')
            if aadhar_back_image:
                driver.aadhar_back_image = aadhar_back_image
            driving_licence_front = request.FILES.get('driving_licence_front')
            if driving_licence_front:
                driver.driving_licence_front = driving_licence_front
            driving_licence_back = request.FILES.get('driving_licence_back')
            if driving_licence_back:
                driver.driving_licence_back = driving_licence_back
            police_verification = request.FILES.get('police_verification')
            if police_verification:
                driver.police_verification = police_verification
            driving_licence_number = request.POST.get('driving_licence_number')
            if driving_licence_number:
                driver.driving_licence_number = driving_licence_number
            driving_licence_expiry_date = request.POST.get(
                'driving_licence_expiry_date')
            if driving_licence_expiry_date:
                driver.driving_licence_expiry_date = driving_licence_expiry_date
            taxi_badge_number = request.POST.get('taxi_badge_number')
            if taxi_badge_number:
                driver.taxi_badge_number = taxi_badge_number
            cab_noc_agreement = request.POST.get('cab_noc_agreement')
            if cab_noc_agreement:
                driver.cab_noc_agreement = cab_noc_agreement
            driver.save()
            e = Event(
                driver=driver,
                username=owner.user.name,
                email=owner.user.email,
                text='Driver added by ' + owner.user.name
            )
            e.save()
            messages.success(request, 'Profile Created Successfully')
            return redirect('vendor_drivers')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'drform': drform, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "owner_driver_details.html", data)
    else:
        return redirect('login_page')


def vendor_edit_driver(request, driver_id):
    print(f'POST: {request.POST}\nFILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_dashboard')
        if owner.is_owner:
            return redirect('owner_details')
        driver = DriverProfile.objects.filter(pk=driver_id).first()
        if not driver:
            return redirect('vendor_drivers')
        drform = driver_form(instance=driver)
        if request.POST:
            driver.name = request.POST.get('name')
            driver.phone = request.POST.get('phone')
            picture = request.FILES.get('picture')
            if picture:
                driver.picture = picture
            aadhar_card_number = request.POST.get('aadhar_card_number')
            if aadhar_card_number:
                driver.aadhar_card_number = aadhar_card_number
            aadhar_front_image = request.FILES.get('aadhar_front_image')
            if aadhar_front_image:
                driver.aadhar_front_image = aadhar_front_image
            aadhar_back_image = request.FILES.get('aadhar_front_image')
            if aadhar_back_image:
                driver.aadhar_back_image = aadhar_back_image
            driving_licence_front = request.FILES.get('driving_licence_front')
            if driving_licence_front:
                driver.driving_licence_front = driving_licence_front
            driving_licence_back = request.FILES.get('driving_licence_back')
            if driving_licence_back:
                driver.driving_licence_back = driving_licence_back
            driving_licence_number = request.POST.get('driving_licence_number')
            if driving_licence_number:
                driver.driving_licence_number = driving_licence_number
            driving_licence_expiry_date = request.POST.get(
                'driving_licence_expiry_date')
            if driving_licence_expiry_date:
                driver.driving_licence_expiry_date = driving_licence_expiry_date
            taxi_badge_number = request.POST.get('taxi_badge_number')
            if taxi_badge_number:
                driver.taxi_badge_number = taxi_badge_number
            driver.save()
            e = Event(
                driver=driver,
                username=owner.user.name,
                email=owner.user.email,
                text='Driver profile updated by ' + owner.user.name
            )
            e.save()
            messages.success(request, 'Profile Updated Successfully')
            return redirect('vendor_drivers')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'drform': drform, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, "owner_driver_details.html", data)
    else:
        return redirect('login_page')


def vendor_post_trip(request):
	print(f'THIS IS POST: {request.POST}')
	print(f'THIS IS GET: {request.GET}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		if profile:
			return redirect('customer_dashboard')
		if owner.is_owner:
			return redirect('owner_posted_trips')
		if not owner.is_active:
			messages.error(request, 'Sorry! Please contact customer care to activate your account.')
			return redirect('dashboard')
		# Confirm Booking 
		if request.POST.get('confirm_without_traveller'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('car_type')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			days = request.GET.get('days')
			vendor_amount = request.GET.get('vendor_amount')
			if days == 'None':
				days = 0
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('vendor_post_trip')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			total_time = time + 2.0
			pickup_temp_date = datetime.datetime.strptime(pickup_date, '%Y-%m-%d')
			pickup_temp_time = datetime.datetime.strptime(pickup_time, '%H:%M').time()
			pickup_datetime = datetime.datetime.combine(pickup_temp_date, pickup_temp_time)
			drop_datetime = pickup_datetime + datetime.timedelta(days=int(days), hours=total_time)
			print(f'ptd: {pickup_temp_date} ptt: {pickup_temp_time} pdatetime: {pickup_datetime} drop_datetime: {drop_datetime}')
			car_type = CarType.objects.get(pk=car_type_id)
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			# New Trip generation
			trip = VendorTrip()
			trip.pickup_city = pickup_city
			trip.pickup_state = pickup_state
			trip.drop_city = drop_city
			trip.drop_state = drop_state
			trip.customer = profile
			trip.pickup_date = pickup_date
			trip.pickup_time = pickup_time
			trip.drop_time = drop_datetime
			trip.car_type = car_type
			print(f'PICKUP CORDS: {pickup_cordinates} DROP CORDS: {drop_cordinates}')
			trip.pickup_location = pickup_cordinates
			trip.drop_location = drop_cordinates
			trip.pickup_address = pickup_address
			trip.drop_address = drop_address
			if trip_type == 'round':
				trip.round_trip = True
				trip.days = days
			trip.vendor_amount = vendor_amount
			trip.distance = distance
			trip.poster = owner
			trip.is_verified = True
			trip.save()
			tdate = trip.pickup_date
			tdate = tdate.replace('-','')	
			ttime = trip.pickup_time
			ttime = ttime.replace(':','')
			trip_no_str = tdate + ttime + '000000'
			trip_no_str = str(int(trip_no_str) + int(trip.id))
			trip.trip_no = trip_no_str
			trip.save()
			print(f'AFTER SAVE PICKUP CORDS: {trip.pickup_location} DROP CORDS: {trip.drop_location}')
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip created by ' + owner.user.name 
			)
			e.save()
			return redirect('vendor_posted_trips')
		if request.POST.get('confirm_booking'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('car_type')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			days = request.GET.get('days')
			vendor_amount = request.GET.get('vendor_amount')
			if days == 'None':
				days = 0
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('vendor_post_trip')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			total_time = time + 2.0
			pickup_temp_date = datetime.datetime.strptime(pickup_date, '%Y-%m-%d')
			pickup_temp_time = datetime.datetime.strptime(pickup_time, '%H:%M').time()
			pickup_datetime = datetime.datetime.combine(pickup_temp_date, pickup_temp_time)
			drop_datetime = pickup_datetime + datetime.timedelta(days=int(days), hours=total_time)
			print(f'ptd: {pickup_temp_date} ptt: {pickup_temp_time} pdatetime: {pickup_datetime} drop_datetime: {drop_datetime}')
			car_type = CarType.objects.get(pk=car_type_id)
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			# New Trip generation
			trip = VendorTrip()
			trip.pickup_city = pickup_city
			trip.pickup_state = pickup_state
			trip.drop_city = drop_city
			trip.drop_state = drop_state
			trip.customer = profile
			trip.pickup_date = pickup_date
			trip.pickup_time = pickup_time
			trip.drop_time = drop_datetime
			trip.car_type = car_type
			print(f'PICKUP CORDS: {pickup_cordinates} DROP CORDS: {drop_cordinates}')
			trip.pickup_location = pickup_cordinates
			trip.drop_location = drop_cordinates
			trip.pickup_address = pickup_address
			trip.drop_address = drop_address
			if trip_type == 'round':
				trip.round_trip = True
				trip.days = days
			trip.vendor_amount = vendor_amount
			trip.distance = distance
			trip.poster = owner
			trip.is_verified = True
			trip.save()
			tdate = trip.pickup_date
			tdate = tdate.replace('-','')	
			ttime = trip.pickup_time
			ttime = ttime.replace(':','')
			trip_no_str = tdate + ttime + '000000'
			trip_no_str = str(int(trip_no_str) + int(trip.id))
			trip.trip_no = trip_no_str
			trip.save()
			print(f'AFTER SAVE PICKUP CORDS: {trip.pickup_location} DROP CORDS: {trip.drop_location}')
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip created by ' + owner.user.name 
			)
			e.save()
			# Travellers Object
			traveller = TravellersInformation()
			traveller.vendor_trip = trip
			traveller.name = request.POST.get('name')
			traveller.phone = request.POST.get('phone')
			traveller.email = request.POST.get('email')
			traveller.address = request.POST.get('address')
			traveller.no_of_travellers = request.POST.get('no_of_travellers')
			traveller.no_of_bags = request.POST.get('no_of_bags')
			traveller.special_instructions = request.POST.get('special_instructions')
			carrier = False
			if request.POST.get('carrier_required') == 'on':
				carrier = True
			traveller.carrier_required = carrier
			traveller.save()
			return redirect('vendor_posted_trips')
		# Pick up location
		if request.GET.get('pickup_location'):
			pickup_location = request.GET.get('pickup_location')
			trip_type = request.GET.get('trip_type')
			days = request.GET.get('days')
			drop_location = request.GET.get('drop_location')
			trip_perimeter = request.GET.get('trip_perimeter')
			if not drop_location:
				tform = trip_drop(initial={'pickup_location':pickup_location})
				data = {'tform':tform,'trip_type':trip_type, 'days':days, 'trip_perimeter': trip_perimeter}
				return render(request, 'vendor_create_trip.html', data)
		# Drop Location
		if request.GET.get('drop_location'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type = request.GET.get('car_type')
			trip_type = request.GET.get('trip_type')
			days = request.GET.get('days')
			if not car_type:
				if not(pickup_location and drop_location):
					messages.error(request, 'Please enter valid details')
					return redirect('vendor_post_trip')
				pickup_cordinates = pickup_location.split(',')
				drop_cordinates = drop_location.split(',')
				pickup_cordinates.reverse()
				drop_cordinates.reverse()
				distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
				if not distance:
					messages.error(request, 'Please select valid locations')
					return redirect('vendor_post_trip')
				car_types = CarType.objects.filter(is_active=True)
				pickup_address = get_location_address(pickup_cordinates)
				drop_address = get_location_address(drop_cordinates)
				data = {
					'pickup_address':pickup_address,
					'drop_address':drop_address, 
					'car_types': car_types, 
					'pickup_location': pickup_location, 
					'drop_location': drop_location,
					'trip_type': trip_type,
					'days': days,
					'details':details
					}
				return render(request, 'vendor_select_cars.html', data)
		# Select time and car type
		if request.GET.get('car_type'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('car_type')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			vendor_amount = request.GET.get('vendor_amount')
			days = request.GET.get('days')
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('vendor_post_trip')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			car_type = CarType.objects.get(pk=car_type_id)
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			trform = traveller_form()
			data = {
				'vendor_amount':vendor_amount,
				'pickup_address':pickup_address,
				'drop_address':drop_address, 
				'pickup_location':pickup_location, 
				'pickup_time': pickup_time,
				'pickup_date': pickup_date,
				'drop_location':drop_location, 
				'trform': trform, 
				'distance': distance,
				'trip_type': trip_type,
				'days': days,
				'car_type':car_type,
				'distance': round(distance, 2),
				'details':details
				}
			return render(request, 'vendor_confirm_booking.html', data)
		tform = trip_pickup()
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		data = {'tform':tform, 'notify':unseen_notifications, 'unseen_count': unseen_count}
		return render(request, 'vendor_create_trip.html', data)
	else:
		return redirect('login_page')

def customer_dashboard(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'details': details, 'notify': unseen_notifications,
                'unseen_count': unseen_count}
        return render(request, 'customer_dashboard.html', data)
    else:
        return redirect('login_page')


def customer_details(request):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		if profile.is_corporate == True:
			corp_profile = CorporateCustomerProfile.objects.get(user = profile)
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		if request.POST.get('profile_pic_update'):
			profile.profile_picture = request.FILES.get('profile_pic')
			profile.save()
			e = Event(
				customer = profile,
				username = profile.user.name,
				email = profile.user.email,
				text = 'Customer profile picture updated by ' + profile.user.name 
			)
			e.save()
			messages.success(request, 'Profile picture updated successfully')
			return redirect('customer_details')
		if request.POST.get('update_profile'):
			details.name = request.POST.get('name')
			details.contact = request.POST.get('contact')
			details.save()
			if profile.is_corporate == True:
				corp_profile.pan = request.POST.get('pan')
				corp_profile.pan_image = request.POST.get('pan_image')
				corp_profile.gst = request.POST.get('gst')
				corp_profile.save()
			add_cord = request.POST.get('address')
			if add_cord != '':
				add_cord = add_cord.split(',')
				add_cord.reverse()
				address_text = get_location_address(add_cord)
				profile.address_text = address_text
			profile.address = add_cord
			profile.save()
			e = Event(
				customer = profile,
				username = profile.user.name,
				email = profile.user.email,
				text = 'Customer profile updated by ' + profile.user.name 
			)
			e.save()
			messages.success(request, 'Profile updated successfully')
			return redirect('customer_details')
		cform = customer_address_form(instance=profile)
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		if profile.is_corporate == True:
			data = {'profile': profile, 'details':details, 'cform':cform, 'notify':unseen_notifications, 'unseen_count': unseen_count, 'corp_profile': corp_profile}
		else:
			data = {'profile': profile, 'details':details, 'cform':cform, 'notify':unseen_notifications, 'unseen_count': unseen_count}
		return render(request, 'customer_profile.html', data) 
	else:
		return redirect('login_page')

def customer_create_trip(request):
	print(f'THIS IS POST: {request.POST}')
	print(f'THIS IS GET: {request.GET}')
	# required for crate trip added by vignesh
	vehicle_groups = VehicalGroup.objects.only('name')
	trip_types = Charges.TRIP_TYPE_CHOICES
	trip_ways = Charges.TRIP_WAY_CHOICES
	trip_variants = Charges.TRIP_VARIANT_CHOICES

	# if request.user.is_authenticated:
	# 	# New Trip generation
	trip = Trip()
	if request.user.is_superuser:
		return redirect('admin_dashboard')
	details = detail.objects.filter(email=request.user.email).first() if request.user.is_authenticated else None
	owner = OwnerProfile.objects.filter(user=details).first() if request.user.is_authenticated else None
	profile = CustomerProfile.objects.filter(user=details).first() if request.user.is_authenticated else None
	if owner:
		if owner.is_owner:
			return redirect('owner_dashboard')
		else:
			return redirect('vendor_dashboard')
	if request.POST.get('razorpay_signature'):
		razorpay_payment_id = request.POST.get('razorpay_payment_id')
		razorpay_order_id = request.POST.get('razorpay_order_id')
		razorpay_signature = request.POST.get('razorpay_signature')
		razorData = {'razorpay_payment_id':razorpay_payment_id, 'razorpay_order_id':razorpay_order_id, 'razorpay_signature':razorpay_signature}
		client = razorpay.Client(auth=(razorpay_id, razorpay_secret))
		client.utility.verify_payment_signature(razorData)
		transaction = Transaction.objects.get(razorpay_order_id=razorpay_order_id)
		transaction.razorpay_payment_id = razorpay_payment_id
		transaction.razorpay_signature = razorpay_signature
		transaction.status = "Paid Successfully"
		transaction.save()
		paymentdetail = transaction.paymentdetail
		paymentdetail.customer_balance += transaction.amount
		paymentdetail.save()
		customer_wallet = profile.wallet.first()
		customer_wallet.balance += transaction.amount
		customer_wallet.save()
		payment_type = request.POST.get('payment_type')
		if payment_type == 'trip_full_payment':
			paymentdetail.final_payment = transaction.amount
			paymentdetail.save()
			messages.success(request, 'Trip full payment made successfully!')
		if payment_type == 'trip_partial_payment':
			paymentdetail.partial_payment = transaction.amount
			paymentdetail.save()
			messages.success(request, 'Trip partial payment made successfully!')
		return redirect('customer_my_trips')
	# Confirm Booking 
	if request.POST.get('confirm_booking'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('vehicle_type')
			car_type = request.GET.get('car_type')
			vehicle_name = request.GET.get('vehicle_name')
			vehicle_company = request.GET.get('vehicle_company')
			vehicle_type = request.GET.get('vehicle_type')
			vehicle_group = request.GET.get('vehicle_group')
			trip_way = request.GET.get('trip_way')
			trip_variant = request.GET.get('trip_variant')
			selected_trip_type = request.GET.get('trip_type')
			days = request.GET.get('days')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			print(f"\npickup_location: {pickup_location}\ndrop_location: {drop_location}\ntrip_way: {trip_way}\ntrip_variant: {trip_variant}\ntrip_type: {selected_trip_type}\nvehicle_group: {vehicle_group}\nvehicle_type: {vehicle_type}\nVehicle_company: {vehicle_company}\nvehicle_name: {vehicle_name}\npickup_date: {pickup_date}\npickup_time: {pickup_time}\ndays: {days}\n")
			
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('customer_create_trip')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			total_time = time + 2.0
			pickup_temp_date = datetime.datetime.strptime(pickup_date, '%Y-%m-%d')
			pickup_temp_time = datetime.datetime.strptime(pickup_time, '%H:%M').time()
			pickup_datetime = datetime.datetime.combine(pickup_temp_date, pickup_temp_time)
			drop_datetime = pickup_datetime + datetime.timedelta(days=int(days), hours=total_time)
			print(f'ptd: {pickup_temp_date} ptt: {pickup_temp_time} pdatetime: {pickup_datetime} drop_datetime: {drop_datetime}')
			# car_type = CarType.objects.get(pk=1)
			pickup_address = get_location_address(pickup_cordinates)
			
			drop_address = get_location_address(drop_cordinates)
			print("pickup_address",pickup_address,"\n","drop_address",drop_address)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			print("vehicle_type",vehicle_type)

			trip_cost = getCharges(request,vehicle_group,vehicle_type, selected_trip_type,trip_variant, trip_way,distance,time,pickup_time,pickup_date,days[0],pickup_city,drop_city)
			print("\nFinal_Trip_Cost ",trip_cost["Final_Trip_Cost"])
			
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			
			# print(trip.rejected_by,"before deletion")
			# trip.rejected_by.clear()
			# print(trip.rejected_by,"after deletion")
			trip.pickup_city = pickup_city
			trip.pickup_state = pickup_state
			trip.drop_city = drop_city
			trip.drop_state = drop_state
			trip.customer = profile
			trip.pickup_date = pickup_date
			trip.pickup_time = pickup_time
			trip.drop_time = drop_datetime
			trip.car_type = VehicalType.objects.get(name=vehicle_type)
			print(f'PICKUP CORDS: {pickup_cordinates} DROP CORDS: {drop_cordinates}')
			trip.pickup_location = pickup_cordinates
			trip.drop_location = drop_cordinates
			trip.pickup_address = pickup_address
			trip.drop_address = drop_address
			if trip_type == 'round':
				trip.round_trip = True
				trip.days = days[0]
			trip.bill_amount = trip_cost["Final_Trip_Cost"]  #116
			trip.fare = trip_cost["Effective_Trip_Cost"]# int(charges_before_tax) #141
			trip.tax = trip_cost["gst"] #int(charges_before_tax * tax_percent/100)
			trip.day_charges = trip_cost["base_cost"] #day_charges
			trip.extra_dist_charges = trip_cost["applicable_charges"] #int(extra_dist_charges)
			trip.total_driver_allowance = trip_cost["total_driver_allowance"]
			trip.tax_percent = 5 #tax_percent
			trip.distance = distance
			trip.save()
			tdate = trip.pickup_date
			tdate = tdate.replace('-','')	
			ttime = trip.pickup_time
			ttime = ttime.replace(':','')
			trip_no_str = tdate + ttime + '000000'
			trip_no_str = str(int(trip_no_str) + int(trip.id))
			trip.trip_no = trip_no_str
			trip.save()
			print(f'AFTER SAVE PICKUP CORDS: {trip.pickup_location} DROP CORDS: {trip.drop_location}')
			e = Event(
				trip = trip,
				username = profile.user.name,
				email = profile.user.email,
				text = 'Trip created by ' + profile.user.name 
			)
			e.save()
			# Travellers Object
			traveller = TravellersInformation()
			traveller.trip = trip
			traveller.name = request.POST.get('name')
			traveller.phone = request.POST.get('phone')
			traveller.email = request.POST.get('email')
			traveller.address = request.POST.get('address')
			traveller.no_of_travellers = request.POST.get('no_of_travellers')
			traveller.no_of_bags = request.POST.get('no_of_bags')
			traveller.special_instructions = request.POST.get('special_instructions')
			carrier = False
			if request.POST.get('carrier_required') == 'on':
				carrier = True
			traveller.carrier_required = carrier
			traveller.save()
			method = request.POST.get('payment_method')
			if method == 'full_payment':
				trip.generate_payment_detail_advance()
				payment_detail = trip.payment_detail.first()
				redeem_amount =trip_cost["redeem_wallet"]
				wallet = profile.wallet.first()
				wallet.customer_redeem(payment_detail, redeem_amount)
				trip.is_verified = False
				trip.save()
				trip.generate_otp()
				razorpay_od_id = wallet.customer_to_company_generate_trip_transaction(payment_detail)
				data = {'razorpay_od_id':razorpay_od_id, 'amount':payment_detail.customer_balance, 'profile':profile, 'type': 'trip_full_payment', 'trip':trip}
				return render(request, 'customer_trip_make_payment.html',data)
			elif method == 'partial_paymnet':
				trip.generate_payment_detail_advance()
				payment_detail = trip.payment_detail.first()
				redeem_amount = trip.car_type.redeem_wallet_amount
				wallet = profile.wallet.first()
				wallet.customer_redeem(payment_detail, redeem_amount)
				trip.is_verified = False
				trip.save()
				trip.generate_otp()
				razorpay_od_id = wallet.customer_to_company_generate_trip_advance_transaction(payment_detail)
				data = {'razorpay_od_id':razorpay_od_id, 'amount':payment_detail.customer_balance, 'profile':profile, 'type': 'trip_partial_payment', 'trip':trip}
				return render(request, 'customer_trip_make_payment.html',data)
			else:
				messages.success(request, 'Trip created successfully')	
				return redirect('customer_view_trip', trip_id=trip.id)
	# Pick up location
	if request.GET.get('pickup_location'):
		pickup_location = request.GET.get('pickup_location')
		trip_type = request.GET.get('trip_type')
		days = request.GET.get('days')			
		drop_location = request.GET.get('drop_location')
		vehicle_name = request.GET.get('vehicle_name')
		vehicle_company = request.GET.get('vehicle_company')
		vehicle_type = request.GET.get('vehicle_type')
		vehicle_group = request.GET.get('vehicle_group')
		trip_way = request.GET.get('trip_way')
		trip_variant = request.GET.get('trip_variant')
		trip_type = request.GET.get('trip_type')
		pickup_date = request.GET.get('pickup_date')
		pickup_time= request.GET.get('pickup_time')
		selected = {
			'vehicle_name': vehicle_name,
			'vehicle_company': vehicle_company,
			'vehicle_type': vehicle_type,
			'vehicle_group': vehicle_group,
			'trip_way': trip_way,
			'trip_variant': trip_variant,
			'trip_type': trip_type,
			'pickup_date':pickup_date,
			'pickup_time': pickup_time,
			'days':days

		}
		print(f"\npickup_location: {pickup_location}\ndrop_location: {drop_location}\ntrip_way: {trip_way}\ntrip_variant: {trip_variant}\ntrip_type: {trip_type}\nvehicle_group: {vehicle_group}\nvehicle_type: {vehicle_type}\nVehicle_company: {vehicle_company}\nvehicle_name: {vehicle_name}\npickup_date: {pickup_date}\npickup_time: {pickup_time}\ndays: {days}\n")

		if not drop_location:
			tform = trip_drop(initial={'pickup_location':pickup_location})
			data = {'tform':tform,'trip_types':trip_types,  'vehicle_groups': vehicle_groups, 'trip_ways': trip_ways, 'trip_variants': trip_variants, 'selected': selected}
			return render(request, 'customer_create_trip.html', data)
	# Drop Location
	if request.GET.get('drop_location'):
		pickup_location = request.GET.get('pickup_location')
		drop_location = request.GET.get('drop_location')
		vehicle_name = request.GET.get('vehicle_name')
		vehicle_company = request.GET.get('vehicle_company')
		vehicle_type = request.GET.get('vehicle_type')
		vehicle_group = request.GET.get('vehicle_group')
		trip_way = request.GET.get('trip_way')
		trip_variant = request.GET.get('trip_variant')
		selected_trip_type = request.GET.get('trip_type')
		days = request.GET.get('days')
		trip_perimeter = request.GET.get('trip_perimeter')
		pickup_time = request.GET.get('pickup_time')
		pickup_date = request.GET.get('pickup_date')
		print(f"\npickup_location: {pickup_location}\ndrop_location: {drop_location}\ntrip_way: {trip_way}\ntrip_variant: {trip_variant}\ntrip_type: {selected_trip_type}\nvehicle_group: {vehicle_group}\nvehicle_type: {vehicle_type}\nVehicle_company: {vehicle_company}\nvehicle_name: {vehicle_name}\npickup_date: {pickup_date}\npickup_time: {pickup_time}\ndays: {days}\n")

		selected = {
			'pickup_location':pickup_location,
			'drop_location':drop_location,
			'vehicle_name': vehicle_name,
			'vehicle_company': vehicle_company,
			'vehicle_type': vehicle_type,
			'vehicle_group': vehicle_group,
			'trip_way': trip_way,
			'trip_variant': trip_variant,
			'trip_type': trip_type,
			'pickup_date':pickup_date,
			'pickup_time': pickup_time,
			'days':days
		}
		# Vehicle types
		if not vehicle_type:
			if not(pickup_location and drop_location and trip_way and trip_variant and selected_trip_type):
				messages.error(request, 'Please enter valid details')
				return redirect('customer_create_trip')
			pickup_cordinates = pickup_location.split(',')
			# print("\npickup_cordinates ",pickup_cordinates)
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			# print(distance, time,"distance")
			if not distance:
				messages.error(request, 'Please select valid locations')
				return redirect('customer_create_trip')
			pickup_address = get_location_address(pickup_cordinates)			
			drop_address = get_location_address(drop_cordinates)
			# print("pickup_address",pickup_address,"\n","drop_address",drop_address)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			# print("vehicle_type",vehicle_type)
			vehicle_types=VehicalType.objects.filter(group=vehicle_group)
			# print(vehicle_types)
			vehicle_types_data=[]
			for types in vehicle_types:
				# print(types.pk)
				vehicle_type_info= VehicalType.objects.get(pk=types.pk)
				full_charges = getCharges(request,vehicle_group,types.pk, selected_trip_type,trip_variant, trip_way,distance,time,pickup_time,pickup_date,days[0],pickup_city,drop_city)
				# print(types.pk,"charges ",full_charges)
				if full_charges != None:
					vehicle_types_data.append({'vehicle_type_info':vehicle_type_info,'charges_list':full_charges})
			if not vehicle_types_data:
				messages.warning(
            request, f"The {selected.get('trip_type')} {selected.get('trip_variant')} {selected.get('trip_way')} type trip is not available on {selected.get('vehicle_group')}, try others...")
				return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			available_cars = VehicalName.objects.filter( type=vehicle_type, group=vehicle_group)
			# print(available_cars)
			data = {
				'pickup_address':pickup_address,
				'drop_address':drop_address,  
				'vehicle_types_data':vehicle_types_data,
				'available_cars': available_cars,
				'vehicle_groups':vehicle_groups,	
				'trip_ways':trip_ways,
				'trip_variants':trip_variants,
				'trip_types':trip_types,				
				'selected':selected,
				}
			print(data)
			return render(request, 'customer_select_vehicle_type.html', data)
	
		# Vehicle name
		if not vehicle_name:
			if not(pickup_location and drop_location and trip_way and trip_variant and selected_trip_type):
				messages.error(request, 'Please enter valid details')
				return redirect('customer_create_trip')
			pickup_cordinates = pickup_location.split(',')
			# print("\npickup_cordinates ",pickup_cordinates)
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			if not distance:
				messages.error(request, 'Please select valid locations')
				return redirect('customer_create_trip')
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			# print("pickup_address",pickup_address,"\n","drop_address",drop_address)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			# print("vehicle_type",vehicle_type)
			
			
			full_charges = getCharges(request,vehicle_group,vehicle_type, selected_trip_type,trip_variant, trip_way,distance,time,pickup_time,pickup_date,days[0],pickup_city,drop_city)
			
			if full_charges == "None":
				messages.warning(
            request, f"The {selected.get('trip_type')} {selected.get('trip_variant')} {selected.get('trip_way')} type trip is not available on {selected.get('vehicle_type')}, try others...")
				return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			vehicle_type_obj=VehicalType.objects.get(name=vehicle_type)
			available_cars = VehicalName.objects.filter( type=vehicle_type, group=vehicle_group)
			print(available_cars)
			data = {
				'pickup_address':pickup_address,
				'drop_address':drop_address, 
				'total_charges': full_charges,
				'vehicle_type_data':vehicle_type_obj,
				'available_cars': available_cars,			
				'selected':selected,
				'distance': round(distance, 2),
				}
			# print(data)
			return render(request, 'customer_select_cars.html', data)

		

		print("selected car ",vehicle_name)
		if not(pickup_location and drop_location and vehicle_type and vehicle_name and pickup_time and pickup_date and trip_way and trip_variant and selected_trip_type):
			messages.error(request, 'Please enter valid details')
			return redirect('customer_create_trip')
		
		pickup_cordinates = pickup_location.split(',')
		print("\npickup_cordinates ",pickup_cordinates)
		drop_cordinates = drop_location.split(',')
		pickup_cordinates.reverse()
		drop_cordinates.reverse()
		print(pickup_cordinates,"hereeeeeee")
		distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
		print(distance, time,"distance")
		if not distance:
			messages.error(request, 'Please select valid locations')
			return redirect('customer_create_trip')
		# car_types = CarType.objects.filter(is_active=True)
		pickup_address = get_location_address(pickup_cordinates)
		
		drop_address = get_location_address(drop_cordinates)
		print("pickup_address",pickup_address,"\n","drop_address",drop_address)
		pickup_city, pickup_state = get_state_and_city(pickup_address)
		drop_city, drop_state = get_state_and_city(drop_address)
		print("vehicle_type",vehicle_type)
		selected_vehicle=VehicalName.objects.get(name=vehicle_name)

		trip_cost = getCharges(request,vehicle_group,vehicle_type, selected_trip_type,trip_variant, trip_way,distance,time,pickup_time,pickup_date,days[0],pickup_city,drop_city)
		
		if trip_cost == "None":
			messages.warning(
		request, f"The {selected.get('trip_type')} {selected.get('trip_variant')} {selected.get('trip_way')} type trip is not available on {selected.get('vehicle_type')}, try others...")
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
		pickup_address = get_location_address(pickup_cordinates)
		drop_address = get_location_address(drop_cordinates)
		trform = traveller_form()
		final_form = trip_final_form()
	

		data = {	
			'pickup_address':pickup_address,
			'drop_address':drop_address,  
			'trform': trform, 
			'final_form': final_form,
			'selected_vehicle':selected_vehicle,
			'trip_cost':trip_cost,
			'selected':selected,
			'distance': round(distance, 2),
			}
		print(f'\n\n\n\n\n{data}\n\n\n\n\n')
		return render(request, 'customer_confirm_trip.html', data)
	if profile and profile.address:
		tform = trip_pickup(initial={'pickup_location':profile.address})
	else:
		tform = trip_pickup()

	
	selected = {
		'vehicle_name': "",
		'vehicle_company': "",
		'vehicle_type': "",
		'vehicle_group': "car",
		'trip_way': "",
		'trip_variant': "LOCAL",
		'trip_type': "RENTAL",
		'days':1,
	}
	data = {'tform': tform, 'vehicle_groups': vehicle_groups, 'selected': selected,
			'trip_types': trip_types, 'trip_ways': trip_ways, 'trip_variants': trip_variants}
	return render(request, 'customer_create_trip.html', data)


def customer_edit_pickup(request, trip_id):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		trip = Trip.objects.get(pk=trip_id)
		if request.POST.get('pickup_location'):
			pickup_location = request.POST.get('pickup_location')
			days = request.GET.get('days')
			pickup_cordinates = pickup_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates = trip.drop_location
			pickup_address = get_location_address(pickup_cordinates)
			if pickup_address == 'Invalid Address':
				messages.error(request, 'Please Select Valid Address')
				return redirect('customer_edit_pickup', trip_id=trip.id)
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			trip_type = 'round' if trip.round_trip else 'oneway'
			car_type = trip.car_type
			final_charges = 0
			trip_perimeter = request.GET.get('trip_perimeter')
			if trip_perimeter == 'local':
				if time_frame == "morning":
					surge_charge = distance*car_type.local_morning_surge_charge
				elif time_frame == "evening":
					surge_charge = distance*car_type.local_evening_surge_charge
				elif time_frame == "night":
					surge_charge = distance*car_type.local_night_surge_charge
				surge_charge = surge_charge + trip.toll_charges + car_type.permit
				if trip_type == 'oneway':
					temp_dist = distance - car_type.local_oneway_min_km 
					
					# If distance is more than minumum distance
					if temp_dist > 0:
						extra_dist_charges = car_type.local_oneway_rate_per_km*temp_dist
						charges = car_type.local_oneway_min_charge + extra_dist_charges + surge_charge
					else:
						extra_dist_charges = 0
						charges = car_type.local_oneway_min_charge
					tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
					day_based = False
					day_charges = False
					total_driver_allowance = 0
					charges -= car_type.redeem_wallet_amount
					charges_before_tax = charges
					charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
					charges = int(charges)
					final_charges = charges	
				if trip_type == 'round':
					distance = int(distance) * 2
					days = int(days)
					temp_dist = distance - car_type.local_round_min_km
					
					day_dist = car_type.local_round_min_km * days
					if distance < day_dist:
						day_based = True
						extra_dist_charges = 0
						day_charges = car_type.local_round_min_charge * days
						charges = int(day_charges)
					else:
						day_based = False
						day_charges = False
						if temp_dist > 0:
							extra_dist_charges = car_type.local_round_rate_per_km * temp_dist
							charges = car_type.local_round_min_charge + extra_dist_charges + surge_charge
							charges = charges
						else:
							extra_dist_charges = 0
							charges = car_type.local_round_min_charge
							charges = charges
					# Driver allowance
					total_driver_allowance = car_type.local_round_driver_allowance * days
					charges += total_driver_allowance
					charges -= car_type.redeem_wallet_amount
					charges_before_tax = int(charges)
					tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
					charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100)) 
					final_charges = int( charges )
			if trip_perimeter == 'outstation':
				if time_frame == "morning":
					surge_charge = distance*car_type.outstation_morning_surge_charge
				elif time_frame == "evening":
					surge_charge = distance*car_type.outstation_evening_surge_charge
				elif time_frame == "night":
					surge_charge = distance*car_type.outstation_night_surge_charge
				surge_charge = surge_charge + trip.toll_charges + car_type.permit
				if trip_type == 'oneway':
					temp_dist = distance - car_type.outstation_oneway_min_km 
					
					# If distance is more than minumum distance
					if temp_dist > 0:
						extra_dist_charges = car_type.outstation_oneway_rate_per_km*temp_dist
						charges = car_type.outstation_oneway_min_charge + extra_dist_charges + surge_charge + car_type.oustation_oneway_stay_charge
					else:
						extra_dist_charges = 0
						charges = car_type.outstation_oneway_min_charge + car_type.oustation_oneway_stay_charge
					tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
					day_based = False
					day_charges = False
					total_driver_allowance = 0
					charges -= car_type.redeem_wallet_amount
					charges_before_tax = charges
					charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
					charges = int(charges)
					final_charges = charges	
				if trip_type == 'round':
					distance = int(distance) * 2
					days = int(days)
					temp_dist = distance - car_type.outstation_round_min_km
					
					day_dist = car_type.outstation_round_min_km * days
					if distance < day_dist:
						day_based = True
						extra_dist_charges = 0
						day_charges = car_type.outstation_round_min_charge * days
						charges = int(day_charges)
					else:
						day_based = False
						day_charges = False
						if temp_dist > 0:
							extra_dist_charges = car_type.outstation_round_rate_per_km * temp_dist
							charges = car_type.outstation_round_min_charge + extra_dist_charges + surge_charge
							charges = charges
						else:
							extra_dist_charges = 0
							charges = car_type.outstation_round_min_charge
							charges = charges
					# Driver allowance
					total_driver_allowance = car_type.outstation_round_driver_allowance * days
					charges += total_driver_allowance
					charges -= car_type.redeem_wallet_amount
					charges_before_tax = int(charges)
					tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
					charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100)) 
					final_charges = int( charges )
			# Saving Updated Data
			trip.pickup_location = pickup_cordinates
			trip.pickup_address = pickup_address
			trip.bill_amount = final_charges
			trip.fare = int(charges_before_tax)
			trip.tax = int(charges_before_tax * tax_percent/100)
			trip.day_charges = day_charges
			trip.extra_dist_charges = int(extra_dist_charges)
			trip.total_driver_allowance = total_driver_allowance
			trip.tax_percent = tax_percent
			trip.distance = distance
			trip.save()
			e = Event(
				trip = trip,
				username = profile.user.name,
				email = profile.user.email,
				text = 'Pickup location updated by ' + profile.user.name 
			)
			e.save()
			return redirect('customer_view_trip',trip_id=trip.id)
		tform = trip_pickup(instance = trip)
		data = {'tform':tform, 'details':details}
		return render(request, 'customer_edit_location.html', data)
	else:
		return redirect('login_page')

def customer_edit_drop(request, trip_id):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		trip = Trip.objects.get(pk=trip_id)
		if request.POST.get('drop_location'):
			drop_location = request.POST.get('drop_location')
			drop_cordinates = drop_location.split(',')
			drop_cordinates.reverse()
			pickup_cordinates = trip.pickup_location
			drop_address = get_location_address(drop_cordinates)
			if drop_address == 'Invalid Address':
				messages.error(request, 'Please Select Valid Address')
				return redirect('customer_edit_drop', trip_id=trip.id)
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			print(f'DIST: {distance}')
			trip_type = 'round' if trip.round_trip else 'oneway'
			car_type = trip.car_type
			days = trip.days
			final_charges = 0
			trip_perimeter = request.GET.get('trip_perimeter')
			if trip_perimeter == 'local':
				if time_frame == "morning":
					surge_charge = distance*car_type.local_morning_surge_charge
				elif time_frame == "evening":
					surge_charge = distance*car_type.local_evening_surge_charge
				elif time_frame == "night":
					surge_charge = distance*car_type.local_night_surge_charge
				surge_charge = surge_charge + trip.toll_charges + car_type.permit
				if trip_type == 'oneway':
					temp_dist = distance - car_type.local_oneway_min_km 
					
					# If distance is more than minumum distance
					if temp_dist > 0:
						extra_dist_charges = car_type.local_oneway_rate_per_km*temp_dist
						charges = car_type.local_oneway_min_charge + extra_dist_charges + surge_charge
					else:
						extra_dist_charges = 0
						charges = car_type.local_oneway_min_charge
					tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
					day_based = False
					day_charges = False
					total_driver_allowance = 0
					charges -= car_type.redeem_wallet_amount
					charges_before_tax = charges
					charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
					charges = int(charges)
					final_charges = charges	
				if trip_type == 'round':
					distance = int(distance) * 2
					days = int(days)
					temp_dist = distance - car_type.local_round_min_km
					
					day_dist = car_type.local_round_min_km * days
					if distance < day_dist:
						day_based = True
						extra_dist_charges = 0
						day_charges = car_type.local_round_min_charge * days
						charges = int(day_charges)
					else:
						day_based = False
						day_charges = False
						if temp_dist > 0:
							extra_dist_charges = car_type.local_round_rate_per_km * temp_dist
							charges = car_type.local_round_min_charge + extra_dist_charges + surge_charge
							charges = charges
						else:
							extra_dist_charges = 0
							charges = car_type.local_round_min_charge
							charges = charges
				if trip_perimeter == 'outstation':
					if time_frame == "morning":
						surge_charge = distance*car_type.outstation_morning_surge_charge
					elif time_frame == "evening":
						surge_charge = distance*car_type.outstation_evening_surge_charge
					elif time_frame == "night":
						surge_charge = distance*car_type.outstation_night_surge_charge
					surge_charge = surge_charge + trip.toll_charges + car_type.permit
					if trip_type == 'oneway':
						temp_dist = distance - car_type.outstation_oneway_min_km 
						
						# If distance is more than minumum distance
						if temp_dist > 0:
							extra_dist_charges = car_type.outstation_oneway_rate_per_km*temp_dist
							charges = car_type.outstation_oneway_min_charge + extra_dist_charges + surge_charge + car_type.oustation_oneway_stay_charge
						else:
							extra_dist_charges = 0
							charges = car_type.outstation_oneway_min_charge + car_type.oustation_oneway_stay_charge
						tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
						day_based = False
						day_charges = False
						total_driver_allowance = 0
						charges -= car_type.redeem_wallet_amount
						charges_before_tax = charges
						charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
						charges = int(charges)
						final_charges = charges	
					if trip_type == 'round':
						distance = int(distance) * 2
						days = int(days)
						temp_dist = distance - car_type.outstation_round_min_km
						
						day_dist = car_type.outstation_round_min_km * days
						if distance < day_dist:
							day_based = True
							extra_dist_charges = 0
							day_charges = car_type.outstation_round_min_charge * days
							charges = int(day_charges)
						else:
							day_based = False
							day_charges = False
							if temp_dist > 0:
								extra_dist_charges = car_type.outstation_round_rate_per_km * temp_dist
								charges = car_type.outstation_round_min_charge + extra_dist_charges + surge_charge
								charges = charges
							else:
								extra_dist_charges = 0
								charges = car_type.outstation_round_min_charge
								charges = charges
				# Driver allowance
				total_driver_allowance = car_type.outstation_round_driver_allowance * days
				charges += total_driver_allowance
				charges -= car_type.redeem_wallet_amount
				charges_before_tax = int(charges)
				tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
				charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100)) 
				final_charges = int( charges )
			# Saving Updated Data
			trip.drop_location = drop_cordinates
			trip.drop_address = drop_address
			trip.bill_amount = final_charges
			trip.fare = int(charges_before_tax)
			trip.tax = int(charges_before_tax * tax_percent/100)
			trip.day_charges = day_charges
			trip.extra_dist_charges = int(extra_dist_charges)
			trip.total_driver_allowance = total_driver_allowance
			trip.tax_percent = tax_percent
			trip.distance = distance
			trip.save()
			e = Event(
				trip = trip,
				username = profile.user.name,
				email = profile.user.email,
				text = 'Drop location updated by ' + profile.user.name 
			)
			e.save()
			return redirect('customer_view_trip',trip_id=trip.id)
		tform = trip_drop(instance = trip)
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		data = {'tform':tform, 'details':details, 'notify':unseen_notifications, 'unseen_count': unseen_count}
		return render(request, 'customer_edit_location.html', data)
	else:
		return redirect('login_page')

def customer_my_trips(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        profile = CustomerProfile.objects.filter(user=details).first()
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        all_trips = profile.trips.all().order_by('-pickup_date')
        temp = []
        for trip in all_trips:
            temp.append([trip, ])
        all_trips = temp
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'trips': all_trips, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, 'customer_my_trips.html', data)
    else:
        return redirect('login_page')


def customer_view_trip(request, trip_id):
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		all_trips = profile.trips.all()
		this_trip = Trip.objects.filter(pk=trip_id).first()
		if not this_trip:
			return redirect('customer_my_trips')
		if this_trip in all_trips:
			trip_type = 'round' if this_trip.round_trip else 'oneway'
			distance = this_trip.distance
			days = this_trip.days
			if request.POST.get('delete'):
				this_trip.delete()
				messages.success(request, 'Trip deleted successfully')
				return redirect('customer_my_trips')
			if request.POST.get('cancel'):
				this_trip.is_canceled = True
				this_trip.save()
				e = Event(
					trip = this_trip,
					username = profile.user.name,
					email = profile.user.email,
					text = 'Trip cancelled by ' + profile.user.name 
				)
				e.save()
				messages.success(request, 'Trip cancelled successfully')
				return redirect('customer_view_trip', trip_id=this_trip.id)
			if request.POST.get('time'):
				this_trip.pickup_time = request.POST.get('time')
				this_trip.save()
				e = Event(
					trip = this_trip,
					username = profile.user.name,
					email = profile.user.email,
					text = 'Trip details updated by ' + profile.user.name 
				)
				e.save()
				messages.success(request, 'Pickup time updated successfully')
				return redirect('customer_view_trip', trip_id=this_trip.id)
			if request.POST.get('date'):
				this_trip.pickup_date = request.POST.get('date')
				this_trip.save()
				e = Event(
					trip = this_trip,
					username = profile.user.name,
					email = profile.user.email,
					text = 'Trip details updated by ' + profile.user.name 
				)
				e.save()
				messages.success(request, 'Pickup date updated successfully')
				return redirect('customer_view_trip', trip_id=this_trip.id)
			if request.POST.get('car_type'):
				car_type_id = request.POST.get('car_type')
				car_type = CarType.objects.get(pk=car_type_id)
				final_charges = 0
				trip_perimeter = request.GET.get('trip_perimeter')
				if trip_perimeter == 'local':
					if time_frame == "morning":
						surge_charge = distance*car_type.local_morning_surge_charge
					elif time_frame == "evening":
						surge_charge = distance*car_type.local_evening_surge_charge
					elif time_frame == "night":
						surge_charge = distance*car_type.local_night_surge_charge
					surge_charge = surge_charge + this_trip.toll_charges + car_type.permit
					if trip_type == 'oneway':
						temp_dist = distance - car_type.local_oneway_min_km 
						
						# If distance is more than minumum distance
						if temp_dist > 0:
							extra_dist_charges = car_type.local_oneway_rate_per_km*temp_dist
							charges = car_type.local_oneway_min_charge + extra_dist_charges + surge_charge
						else:
							extra_dist_charges = 0
							charges = car_type.local_oneway_min_charge
						tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
						day_based = False
						day_charges = False
						total_driver_allowance = 0
						charges -= car_type.redeem_wallet_amount
						charges_before_tax = charges
						charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
						charges = int(charges)
						final_charges = charges	
					if trip_type == 'round':
						distance = int(distance) * 2
						days = int(days)
						temp_dist = distance - car_type.local_round_min_km
						
						day_dist = car_type.local_round_min_km * days
						if distance < day_dist:
							day_based = True
							extra_dist_charges = 0
							day_charges = car_type.local_round_min_charge * days
							charges = int(day_charges)
						else:
							day_based = False
							day_charges = False
							if temp_dist > 0:
								extra_dist_charges = car_type.local_round_rate_per_km * temp_dist
								charges = car_type.local_round_min_charge + extra_dist_charges + surge_charge
								charges = charges
							else:
								extra_dist_charges = 0
								charges = car_type.local_round_min_charge
								charges = charges
						# Driver allowance
						total_driver_allowance = car_type.local_round_driver_allowance * days
						charges += total_driver_allowance
						charges -= car_type.redeem_wallet_amount
						charges_before_tax = int(charges)
						tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
						charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100)) 
						final_charges = int( charges )
				if trip_perimeter == 'outstation':
					if time_frame == "morning":
						surge_charge = distance*car_type.outstation_morning_surge_charge
					elif time_frame == "evening":
						surge_charge = distance*car_type.outstation_evening_surge_charge
					elif time_frame == "night":
						surge_charge = distance*car_type.outstation_night_surge_charge
					surge_charge = surge_charge + this_trip.toll_charges + car_type.permit
					if trip_type == 'oneway':
						temp_dist = distance - car_type.outstation_oneway_min_km 
						
						# If distance is more than minumum distance
						if temp_dist > 0:
							extra_dist_charges = car_type.outstation_oneway_rate_per_km*temp_dist
							charges = car_type.outstation_oneway_min_charge + extra_dist_charges + surge_charge + car_type.oustation_oneway_stay_charge
						else:
							extra_dist_charges = 0
							charges = car_type.outstation_oneway_min_charge + car_type.oustation_oneway_stay_charge
						tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
						day_based = False
						day_charges = False
						total_driver_allowance = 0
						charges -= car_type.redeem_wallet_amount
						charges_before_tax = charges
						charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
						charges = int(charges)
						final_charges = charges	
					if trip_type == 'round':
						distance = int(distance) * 2
						days = int(days)
						temp_dist = distance - car_type.outstation_round_min_km
						
						day_dist = car_type.outstation_round_min_km * days
						if distance < day_dist:
							day_based = True
							extra_dist_charges = 0
							day_charges = car_type.outstation_round_min_charge * days
							charges = int(day_charges)
						else:
							day_based = False
							day_charges = False
							if temp_dist > 0:
								extra_dist_charges = car_type.outstation_round_rate_per_km * temp_dist
								charges = car_type.outstation_round_min_charge + extra_dist_charges + surge_charge
								charges = charges
							else:
								extra_dist_charges = 0
								charges = car_type.outstation_round_min_charge
								charges = charges
						# Driver allowance
						total_driver_allowance = car_type.outstation_round_driver_allowance * days
						charges += total_driver_allowance
						charges -= car_type.redeem_wallet_amount
						charges_before_tax = int(charges)
						tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
						charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100)) 
						final_charges = int( charges )
				this_trip.bill_amount = final_charges
				this_trip.fare = int(charges_before_tax)
				this_trip.tax = int(charges_before_tax * tax_percent/100)
				this_trip.day_charges = day_charges
				this_trip.extra_dist_charges = int(extra_dist_charges)
				this_trip.total_driver_allowance = total_driver_allowance
				this_trip.tax_percent = tax_percent
				this_trip.car_type = car_type
				this_trip.save()
				e = Event(
					trip = this_trip,
					username = profile.user.name,
					email = profile.user.email,
					text = 'Trip details updated by ' + profile.user.name 
				)
				e.save()
				messages.success(request, 'Car type updated successfully')
				return redirect('customer_view_trip', trip_id=this_trip.id)
			if request.POST.get('traveller_edit'):
				tinfo = this_trip.traveller.first()
				trform = traveller_form(request.POST,instance=tinfo)
				if trform.is_valid():
					trform.save()
					e = Event(
						trip = this_trip,
						username = profile.user.name,
						email = profile.user.email,
						text = 'Traveller details updated by ' + profile.user.name 
					)
					e.save()
				else:
					print(f'ERRROR: {trform.errors}')
					messages.error(request, 'Error: Please enter valid data')
					return redirect('customer_view_trip', trip_id=this_trip.id)
				messages.success(request, 'Traveller information updated successfully')
				return redirect('customer_view_trip', trip_id=this_trip.id)
			car_types = CarType.objects.filter(is_active=True)
			type_data = []
			if trip_type == "round":
				for type in car_types:
					round_distance = int(distance) * 2
					days = int(days)
					temp_dist = round_distance - type.local_round_min_km
					day_dist = type.local_round_min_km * days
					if round_distance < day_dist:
						day_based = True
						extra_dist_charges = 0
						day_charges = type.local_round_min_charge * days
						charges = int(day_charges)
					else:
						day_based = False
						day_charges = False
						if temp_dist > 0:
							extra_dist_charges = type.local_round_rate_per_km * temp_dist
							charges = type.local_round_min_charge + extra_dist_charges
							charges = charges
						else:
							extra_dist_charges = 0
							charges = type.local_round_min_charge
							charges = charges
					# Driver allowance
					total_driver_allowance = type.local_round_driver_allowance * days
					charges += total_driver_allowance
					charges -= type.redeem_wallet_amount
					charges_before_tax = int(charges)
					tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
					charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100)) 
					final_charges = int( charges )
					if day_based:
						type.local_round_min_charge = int(day_charges)
					else:
						type.local_round_min_charge = int(charges)
					type.local_round_min_km = int(round_distance)
					type_data.append([type, charges])
			if trip_type == "oneway":	
				for type in car_types:
					temp_dist = distance - type.local_oneway_min_km 
					# If distance is more than minumum distance
					if temp_dist > 0:
						extra_dist_charges = type.local_oneway_rate_per_km*temp_dist
						charges = type.local_oneway_min_charge + extra_dist_charges
					else:
						extra_dist_charges = 0
						charges = type.local_oneway_min_charge
					tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
					total_driver_allowance = 0
					charges -= type.redeem_wallet_amount
					charges_before_tax = charges
					charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
					charges = int(charges)
					final_charges = charges
					type.local_oneway_min_km = int(distance)
					type.local_oneway_min_charge = int(charges)
					type_data.append([type, charges])
			tinfo = this_trip.traveller.first()
			print(tinfo)
			trform = traveller_form(instance=tinfo)
			unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
			all_notifications = list(details.notifications.all().order_by('-date'))
			unseen_count = len(unseen_notifications)
			if len(all_notifications) > 5:
				while len(unseen_notifications) < 5:
					unseen_notifications.append(all_notifications.pop(0))
			else:
				unseen_notifications + all_notifications
			data = {'trip':this_trip, 'car_types':type_data, 'trform':trform, 'details':details, 'notify':unseen_notifications, 'unseen_count': unseen_count}
			return render(request, 'customer_view_trip.html', data)
		else:
			return redirect('customer_my_trips')
	else:
		return redirect('login_page')

def customer_active_bookings(request):
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		# if request.POST.get('start'):
		# 	trip_id = request.POST.get('start')
		# 	trip = Trip.objects.get(pk=trip_id)
		# 	trip.is_started = True
		# 	trip.save()
		# 	e = Event(
		# 		trip = trip,
		# 		username = profile.user.name,
		# 		email = profile.user.email,
		# 		text = 'Trip marked started by ' + profile.user.name
		# 	)
		# 	e.save()
		# 	messages.success(request, 'Trip started successfully')
		# 	return redirect('customer_active_bookings')
		# if request.POST.get('markcomplete'):
		# 	trip_id = request.POST.get('markcomplete')
		# 	trip = Trip.objects.get(pk=trip_id)
		# 	trip.is_complete = True
		# 	trip.save()
		# 	e = Event(
		# 		trip = trip,
		# 		username = profile.user.name,
		# 		email = profile.user.email,
		# 		text = 'Trip marked complete by ' + profile.user.name
		# 	)
		# 	e.save()
		# 	messages.success(request, 'Trip updated successfully')
		# 	return redirect('customer_completed_bookings')
		all_trips = profile.trips.filter(is_complete=False, is_canceled=False).order_by('-pickup_date')
		temp = []
		for trip in all_trips:
			show_complete = False
			drop_time = trip.drop_time + timedelta(hours=2)
			if (datetime.datetime.now() > drop_time) and not trip.is_complete:
				show_complete = True
				print(trip.id)
			show_start = False
			pickup_time = datetime.datetime.combine(trip.pickup_date, trip.pickup_time)
			if (datetime.datetime.now() > pickup_time) and not trip.is_started:
				show_start = True
			print(f'TRIP: {trip} \nPICKUP_TIME: {pickup_time} \nNOW: {datetime.datetime.now()} \nSHOW_START: {show_start} \nDROP_TIME: {drop_time} \nSHOW_COMPLETE: {show_complete}')
			temp.append([trip, show_complete, show_start])
		all_trips = temp
		unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
		all_notifications = list(details.notifications.all().order_by('-date'))
		unseen_count = len(unseen_notifications)
		if len(all_notifications) > 5:
			while len(unseen_notifications) < 5:
				unseen_notifications.append(all_notifications.pop(0))
		else:
			unseen_notifications + all_notifications
		data = {'trips': all_trips, 'active_bookings':True, 'details':details, 'notify':unseen_notifications, 'unseen_count': unseen_count}
		return render(request, 'customer_my_trips.html', data)
	else:
		return redirect('login_page')

def customer_completed_bookings(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        profile = CustomerProfile.objects.filter(user=details).first()
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        all_trips = profile.trips.filter(
            is_complete=True).order_by('-pickup_date')
        temp = []
        for trip in all_trips:
            temp.append([trip, ])
        all_trips = temp
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'trips': all_trips, 'completed': True, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}
        return render(request, 'customer_my_trips.html', data)
    else:
        return redirect('login_page')


def customer_cancelled_bookings(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        profile = CustomerProfile.objects.filter(user=details).first()
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        all_trips = profile.trips.filter(
            is_canceled=True).order_by('-pickup_date')
        temp = []
        for trip in all_trips:
            temp.append([trip, ])
        all_trips = temp
        unseen_notifications = list(
            details.notifications.filter(seen=False).order_by('-date'))
        all_notifications = list(details.notifications.all().order_by('-date'))
        unseen_count = len(unseen_notifications)
        if len(all_notifications) > 5:
            while len(unseen_notifications) < 5:
                unseen_notifications.append(all_notifications.pop(0))
        else:
            unseen_notifications + all_notifications
        data = {'trips': all_trips, 'cancelled': True, 'details': details,
                'notify': unseen_notifications, 'unseen_count': unseen_count}

        return render(request, 'customer_my_trips.html', data)
    else:
        return redirect('login_page')


def admin_dashboard(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        profile = CustomerProfile.objects.filter(user=details).first()
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        elif profile:
            return redirect('customer_dashboard')
        if details:
            if details.is_staff:
                staff = True
            else:
                staff = False
        else:
            staff = False
        if request.user.is_superuser or staff:
            all_trips = Trip.objects.all()
            all_drivers = DriverProfile.objects.all()
            all_owners = OwnerProfile.objects.all()
            all_cars = Car.objects.all()
            all_types = CarType.objects.all()
            all_customers = CustomerProfile.objects.all()
            if staff:
                unseen_notifications = list(
                    details.notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    details.notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            else:
                unseen_notifications = list(
                    request.user.admin_notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    request.user.admin_notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications

            data = {
                'trips': all_trips,
                'drivers': all_drivers,
                'owners': all_owners,
                'cars': all_cars,
                'car_types': all_types,
                'customers': all_customers,
                'staff': staff,
                'notify': unseen_notifications,
                'unseen_count': unseen_count
            }
            return render(request, 'admin_dashboard.html', data)
        else:
            return redirect('logout')
    else:
        return redirect('login_page')


def admin_owner_by_attr(request):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			req = request.POST
			if req['phone'] != '':
				details_list = detail.objects.filter(contact__in = req['phone'].split(','))
				print(details_list)
				all_owners = OwnerProfile.objects.filter(user__in = details_list)
				print(all_owners)
			elif req['name'] != '':
				details_list = detail.objects.filter(contact__in = req['name'].split(','))
				all_owners = OwnerProfile.objects.filter(user__in = details_list)
			elif req['email'] != '':
				details_list = detail.objects.filter(email__in = req['email'].split(','))
				all_owners = OwnerProfile.objects.filter(user__in = details_list)
			if request.POST.get('verify'):
				owner_id = request.POST.get('verify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_verified = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner verified by ' + name
				)
				e.save()
				messages.success(request, 'Verified Successfully')
				return redirect('admin_owners')
			if request.POST.get('unverify'):
				owner_id = request.POST.get('unverify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_verified = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Un-verified Successfully')
				return redirect('admin_owners')
			if request.POST.get('activate'):
				owner_id = request.POST.get('activate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner activated by ' + name
				)
				e.save()
				messages.success(request, 'Activated Successfully')
				return redirect('admin_owners')
			if request.POST.get('deactivate'):
				owner_id = request.POST.get('deactivate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner deactivated by ' + name
				)
				e.save()
				messages.success(request, 'Deactivated Successfully')
				return redirect('admin_owners')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data = {
				'owners': all_owners, 'staff':staff, 'notify':unseen_notifications, 'unseen_count': unseen_count
			}
			return render(request, 'admin_owners.html', data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_owners(request):
    print(f'POST: {request.POST}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        profile = CustomerProfile.objects.filter(user=details).first()
        user = request.user
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        elif profile:
            return redirect('customer_dashboard')
        if details:
            if details.is_staff:
                staff = True
            else:
                staff = False
        else:
            staff = False
        if request.user.is_superuser or staff:
            all_owners = OwnerProfile.objects.all()
            if request.POST.get('verify'):
                owner_id = request.POST.get('verify')
                this_owner = OwnerProfile.objects.get(pk=owner_id)
                this_owner.is_verified = True
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner verified by ' + name
                )
                e.save()
                messages.success(request, 'Verified Successfully')
                return redirect('admin_owners')
            if request.POST.get('unverify'):
                owner_id = request.POST.get('unverify')
                this_owner = OwnerProfile.objects.get(pk=owner_id)
                this_owner.is_verified = False
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner un-verified by ' + name
                )
                e.save()
                messages.success(request, 'Un-verified Successfully')
                return redirect('admin_owners')
            if request.POST.get('activate'):
                owner_id = request.POST.get('activate')
                this_owner = OwnerProfile.objects.get(pk=owner_id)
                this_owner.is_active = True
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner activated by ' + name
                )
                e.save()
                messages.success(request, 'Activated Successfully')
                return redirect('admin_owners')
            if request.POST.get('deactivate'):
                owner_id = request.POST.get('deactivate')
                this_owner = OwnerProfile.objects.get(pk=owner_id)
                this_owner.is_active = False
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner deactivated by ' + name
                )
                e.save()
                messages.success(request, 'Deactivated Successfully')
                return redirect('admin_owners')
            if staff:
                unseen_notifications = list(
                    details.notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    details.notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            else:
                unseen_notifications = list(
                    request.user.admin_notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    request.user.admin_notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            data = {
                'owners': all_owners, 'staff': staff, 'notify': unseen_notifications, 'unseen_count': unseen_count
            }
            return render(request, 'admin_owners.html', data)
        else:
            return redirect('logout')
    else:
        return redirect('login_page')


def admin_verified_owners(request):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_owners = OwnerProfile.objects.filter(is_verified=True)
			if request.POST.get('verify'):
				owner_id = request.POST.get('verify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_verified = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner verified by ' + name
				)
				e.save()
				messages.success(request, 'Verified Successfully')
				return redirect('admin_verified_owners')
			if request.POST.get('unverify'):
				owner_id = request.POST.get('unverify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_verified = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Un-verified Successfully')
				return redirect('admin_verified_owners')
			if request.POST.get('activate'):
				owner_id = request.POST.get('activate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner activated by ' + name
				)
				e.save()
				messages.success(request, 'Activated Successfully')
				return redirect('admin_verified_owners')
			if request.POST.get('deactivate'):
				owner_id = request.POST.get('deactivate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner deactivated by ' + name
				)
				e.save()
				messages.success(request, 'Deactivated Successfully')
				return redirect('admin_verified_owners')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data = {
				'owners': all_owners, 'staff':staff, 'notify':unseen_notifications, 'unseen_count': unseen_count, 'verified_owners':True
			}
			return render(request, 'admin_owners.html', data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_active_owners(request):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_owners = OwnerProfile.objects.filter(is_active=True)
			if request.POST.get('verify'):
				owner_id = request.POST.get('verify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner active by ' + name
				)
				e.save()
				messages.success(request, 'active Successfully')
				return redirect('admin_active_owners')
			if request.POST.get('unverify'):
				owner_id = request.POST.get('unverify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner un-active by ' + name
				)
				e.save()
				messages.success(request, 'Un-active Successfully')
				return redirect('admin_active_owners')
			if request.POST.get('activate'):
				owner_id = request.POST.get('activate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner activated by ' + name
				)
				e.save()
				messages.success(request, 'Activated Successfully')
				return redirect('admin_active_owners')
			if request.POST.get('deactivate'):
				owner_id = request.POST.get('deactivate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner deactivated by ' + name
				)
				e.save()
				messages.success(request, 'Deactivated Successfully')
				return redirect('admin_active_owners')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data = {
				'owners': all_owners, 'staff':staff, 'notify':unseen_notifications, 'unseen_count': unseen_count, 'active_owners':True
			}
			return render(request, 'admin_owners.html', data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_inactive_owners(request):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_owners = OwnerProfile.objects.filter(is_active=False)
			if request.POST.get('verify'):
				owner_id = request.POST.get('verify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner inactive by ' + name
				)
				e.save()
				messages.success(request, 'inactive Successfully')
				return redirect('admin_inactive_owners')
			if request.POST.get('unverify'):
				owner_id = request.POST.get('unverify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner un-inactive by ' + name
				)
				e.save()
				messages.success(request, 'Un-inactive Successfully')
				return redirect('admin_inactive_owners')
			if request.POST.get('activate'):
				owner_id = request.POST.get('activate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner activated by ' + name
				)
				e.save()
				messages.success(request, 'Activated Successfully')
				return redirect('admin_inactive_owners')
			if request.POST.get('deactivate'):
				owner_id = request.POST.get('deactivate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner deactivated by ' + name
				)
				e.save()
				messages.success(request, 'Deactivated Successfully')
				return redirect('admin_inactive_owners')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data = {
				'owners': all_owners, 'staff':staff, 'notify':unseen_notifications, 'unseen_count': unseen_count, 'inactive_owners':True
			}
			return render(request, 'admin_owners.html', data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_unverified_owners(request):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_owners = OwnerProfile.objects.filter(is_verified=False)
			if request.POST.get('verify'):
				owner_id = request.POST.get('verify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_verified = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner verified by ' + name
				)
				e.save()
				messages.success(request, 'Verified Successfully')
				return redirect('admin_unverified_owners')
			if request.POST.get('unverify'):
				owner_id = request.POST.get('unverify')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_verified = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Un-verified Successfully')
				return redirect('admin_unverified_owners')
			if request.POST.get('activate'):
				owner_id = request.POST.get('activate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = True
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner activated by ' + name
				)
				e.save()
				messages.success(request, 'Activated Successfully')
				return redirect('admin_unverified_owners')
			if request.POST.get('deactivate'):
				owner_id = request.POST.get('deactivate')
				this_owner = OwnerProfile.objects.get(pk=owner_id)
				this_owner.is_active = False
				this_owner.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					owner = this_owner,
					username = uname,
					email = email,
					text = 'Owner deactivated by ' + name
				)
				e.save()
				messages.success(request, 'Deactivated Successfully')
				return redirect('admin_unverified_owners')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data = {
				'owners': all_owners, 'staff':staff, 'notify':unseen_notifications, 'unseen_count': unseen_count,'unverified_owners':True
			}
			return render(request, 'admin_owners.html', data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_owner_details(request, owner_id):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        profile = CustomerProfile.objects.filter(user=details).first()
        user = request.user
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        elif profile:
            return redirect('customer_dashboard')
        if details:
            if details.is_staff:
                staff = True
            else:
                staff = False
        else:
            staff = False
        if request.user.is_superuser or staff:
            this_owner = OwnerProfile.objects.filter(pk=owner_id).first()
            details = this_owner.user
            if not this_owner:
                return redirect('admin_dashboard')
            if request.POST.get('verify'):
                profile_type = request.POST.get('profile_type')
                if profile_type == 'driver':
                    this_owner.is_vendor = False
                    this_owner.is_owner = True
                if profile_type == 'vendor':
                    this_owner.is_vendor = True
                    this_owner.is_owner = False
                this_owner.is_verified = True
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner verified by ' + name
                )
                e.save()
                return redirect('admin_owner_details', owner_id=this_owner.id)
            if request.POST.get('unverify'):
                this_owner.is_verified = False
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner un-verified by ' + name
                )
                e.save()
                return redirect('admin_owner_details', owner_id=this_owner.id)
            if request.POST.get('activate'):
                this_owner.is_active = True
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner activated by ' + name
                )
                e.save()
                return redirect('admin_owner_details', owner_id=this_owner.id)
            if request.POST.get('deactivate'):
                this_owner.is_active = False
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner deactivated by ' + name
                )
                e.save()
                return redirect('admin_owner_details', owner_id=this_owner.id)
            if request.POST.get('profile_pic_update'):
                this_owner.profile_picture = request.FILES.get('profile_pic')
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner details updated by ' + name
                )
                e.save()
                messages.success(
                    request, 'Profile picture updated successfully')
                return redirect('admin_owner_details', owner_id=this_owner.id)
            if request.POST.get('update_profile'):
                details.name = request.POST.get('name')
                details.contact = request.POST.get('contact')
                cheque_image = request.FILES.get('cheque_image')
                if cheque_image:
                    this_owner.cheque_image = cheque_image
                this_owner.bank_account_no = request.POST.get(
                    'bank_account_no')
                this_owner.ifsc_code = request.POST.get('ifsc_code')
                this_owner.account_holders_name = request.POST.get(
                    'account_holders_name')
                details.save()
                this_owner.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    owner=this_owner,
                    username=uname,
                    email=email,
                    text='Owner details updated by ' + name
                )
                e.save()
                messages.success(request, 'Profile updated successfully')
                return redirect('admin_owner_details', owner_id=this_owner.id)
            events = this_owner.events.all().order_by('-time')
            if staff:
                unseen_notifications = list(
                    details.notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    details.notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            else:
                unseen_notifications = list(
                    request.user.admin_notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    request.user.admin_notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            data = {
                'profile': this_owner,
                'details': details,
                'staff': staff,
                'events': events,
                'notify': unseen_notifications,
                'unseen_count': unseen_count

            }
            return render(request, 'admin_owner_details.html', data)
        else:
            return redirect('logout')
    else:
        return redirect('login_page')


def admin_car_types(request):
    print(f'POST: {request.POST}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        profile = CustomerProfile.objects.filter(user=details).first()
        user = request.user
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        elif profile:
            return redirect('customer_dashboard')
        if details:
            if details.is_staff:
                staff = True
            else:
                staff = False
        else:
            staff = False
        if request.user.is_superuser or staff:
            car_types = CarType.objects.all()
            if request.POST.get('activate'):
                type_id = request.POST.get('activate')
                type = CarType.objects.get(pk=type_id)
                type.is_active = True
                type.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    car_type=type,
                    username=uname,
                    email=email,
                    text='Car type activated by ' + name
                )
                e.save()
                messages.success(request, 'Car type activated successfully')
                return redirect('admin_car_types')
            if request.POST.get('deactivate'):
                type_id = request.POST.get('deactivate')
                type = CarType.objects.get(pk=type_id)
                type.is_active = False
                type.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    car_type=type,
                    username=uname,
                    email=email,
                    text='Car type deactivated by ' + name
                )
                e.save()
                messages.success(request, 'Car type deactivated successfully')
                return redirect('admin_car_types')
            if staff:
                unseen_notifications = list(
                    details.notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    details.notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            else:
                unseen_notifications = list(
                    request.user.admin_notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    request.user.admin_notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            data = {
                'car_types': car_types,
                'staff': staff,
                'notify': unseen_notifications,
                'unseen_count': unseen_count
            }
            return render(request, 'admin_car_types.html', data)
        else:
            return redirect('logout')
    else:
        return redirect('login_page')


def admin_active_car_types(request):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			car_types = CarType.objects.filter(is_active=True)
			if request.POST.get('activate'):
				type_id = request.POST.get('activate')
				type = CarType.objects.get(pk=type_id)
				type.is_active = True
				type.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car_type = type,
					username = uname,
					email = email,
					text = 'Car type activated by ' + name
				)
				e.save()
				messages.success(request, 'Car type activated successfully')
				return redirect('admin_active_car_types')
			if request.POST.get('deactivate'):
				type_id = request.POST.get('deactivate')
				type = CarType.objects.get(pk=type_id)
				type.is_active = False
				type.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car_type = type,
					username = uname,
					email = email,
					text = 'Car type deactivated by ' + name
				)
				e.save()
				messages.success(request, 'Car type deactivated successfully')
				return redirect('admin_active_car_types')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data = {
				'car_types': car_types,
				'staff':staff, 
				'notify':unseen_notifications, 
				'unseen_count': unseen_count,
				'active_car_type': True
			}
			return render(request, 'admin_car_types.html', data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_deactive_car_types(request):
	print(f'POST: {request.POST}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			car_types = CarType.objects.filter(is_active=False)
			if request.POST.get('activate'):
				type_id = request.POST.get('activate')
				type = CarType.objects.get(pk=type_id)
				type.is_active = True
				type.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car_type = type,
					username = uname,
					email = email,
					text = 'Car type activated by ' + name
				)
				e.save()
				messages.success(request, 'Car type activated successfully')
				return redirect('admin_deactive_car_types')
			if request.POST.get('deactivate'):
				type_id = request.POST.get('deactivate')
				type = CarType.objects.get(pk=type_id)
				type.is_active = False
				type.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car_type = type,
					username = uname,
					email = email,
					text = 'Car type deactivated by ' + name
				)
				e.save()
				messages.success(request, 'Car type deactivated successfully')
				return redirect('admin_deactive_car_types')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data = {
				'car_types': car_types,
				'staff':staff, 
				'notify':unseen_notifications, 
				'unseen_count': unseen_count,
				'deactive_car_type':True
			}
			return render(request, 'admin_car_types.html', data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_edit_car_type(request, type_id):
    print(f'POST: {request.POST} FILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        profile = CustomerProfile.objects.filter(user=details).first()
        user = request.user
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        elif profile:
            return redirect('customer_dashboard')
        if details:
            if details.is_staff:
                staff = True
            else:
                staff = False
        else:
            staff = False
        if request.user.is_superuser or staff:
            if type_id == 0:
                tform = car_type_form()
            else:
                type = CarType.objects.get(pk=type_id)
                tform = car_type_form(instance=type)
            if request.POST:
                if type_id == 0:
                    type_form = car_type_form(request.POST, request.FILES)
                    if type_form.is_valid():
                        type = type_form.save()
                        image = request.FILES.get('picture')
                        print(image)
                        type.picture = image
                        type.save()
                        uname = details.name if staff else 'admin'
                        email = details.email if staff else user.email
                        name = details.name if staff else user.email
                        e = Event(
                            car_type=type,
                            username=uname,
                            email=email,
                            text='Car type added by ' + name
                        )
                        e.save()
                        messages.success(request, 'Type Added Succesfully')
                        return redirect('admin_car_types')
                    else:
                        print(type_form.errors)
                        messages.error(request, 'Error: Cannot save data')
                        return redirect('admin_edit_car_type', type_id=0)
                else:
                    type = CarType.objects.get(pk=type_id)
                    type_form = car_type_form(
                        request.POST, request.FILES, instance=type)

                    if type_form.is_valid():
                        type_form.save()
                        uname = details.name if staff else 'admin'
                        email = details.email if staff else user.email
                        name = details.name if staff else user.email
                        e = Event(
                            car_type=type,
                            username=uname,
                            email=email,
                            text='Car type updated by ' + name
                        )
                        e.save()
                        messages.success(
                            request, 'Type details updated successfully')
                        return redirect('admin_edit_car_type', type_id=type_id)
                    else:
                        messages.error(request, 'Error: Cannot save data')
                        return redirect('admin_edit_car_type', type_id=type_id)
            if type_id != 0:
                events = type.events.all().order_by('-time')
            else:
                events = None
            if staff:
                unseen_notifications = list(
                    details.notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    details.notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            else:
                unseen_notifications = list(
                    request.user.admin_notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    request.user.admin_notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            data = {
                'tform': tform,
                'staff': staff,
                'events': events,
                'notify': unseen_notifications,
                'unseen_count': unseen_count
            }
            return render(request, 'admin_car_type_edit.html', data)
        else:
            return redirect('logout')
    else:
        return redirect('login_page')


def admin_drivers(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_drivers = DriverProfile.objects.all()
			data = {'drivers': all_drivers, 'staff': staff}
			if request.POST.get('unverify'):
				driver_id = request.POST.get('unverify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = False
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver unverified successfully')
				return redirect('admin_drivers')
			if request.POST.get('verify'):
				driver_id = request.POST.get('verify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = True
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver verified successfully')
				return redirect('admin_drivers')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_drivers.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_active_drivers(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			owners = OwnerProfile.objects.filter(is_active=True)
			all_drivers = DriverProfile.objects.filter(owner__in = owners)
			data = {'drivers': all_drivers, 'staff': staff, 'active_drivers':True}
			if request.POST.get('unverify'):
				driver_id = request.POST.get('unverify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = False
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver unverified successfully')
				return redirect('admin_verified_drivers')
			if request.POST.get('verify'):
				driver_id = request.POST.get('verify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = True
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver verified successfully')
				return redirect('admin_verified_drivers')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_drivers.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_inactive_drivers(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			owners = OwnerProfile.objects.filter(is_active=False)
			all_drivers = DriverProfile.objects.filter(owner__in = owners)
			data = {'drivers': all_drivers, 'staff': staff, 'inactive_drivers':True}
			if request.POST.get('unverify'):
				driver_id = request.POST.get('unverify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = False
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver unverified successfully')
				return redirect('admin_verified_drivers')
			if request.POST.get('verify'):
				driver_id = request.POST.get('verify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = True
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver verified successfully')
				return redirect('admin_verified_drivers')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_drivers.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_verified_drivers(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_drivers = DriverProfile.objects.filter(is_verified=True)
			data = {'drivers': all_drivers, 'staff': staff, 'verified_drivers':True}
			if request.POST.get('unverify'):
				driver_id = request.POST.get('unverify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = False
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver unverified successfully')
				return redirect('admin_verified_drivers')
			if request.POST.get('verify'):
				driver_id = request.POST.get('verify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = True
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver verified successfully')
				return redirect('admin_verified_drivers')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_drivers.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_unverified_drivers(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_drivers = DriverProfile.objects.filter(is_verified=False)
			data = {'drivers': all_drivers, 'staff': staff,'unverified_drivers': True}
			if request.POST.get('unverify'):
				driver_id = request.POST.get('unverify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = False
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver unverified successfully')
				return redirect('admin_unverified_drivers')
			if request.POST.get('verify'):
				driver_id = request.POST.get('verify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = True
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver verified successfully')
				return redirect('admin_unverified_drivers')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_drivers.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_drivers_by_attr(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			
			req = request.POST
			if req['phone'] != '':
				print(req['phone'].split(','))
				all_drivers = DriverProfile.objects.filter(phone__in = req['phone'].split(','))
			elif req['name'] != '':
				all_drivers = DriverProfile.objects.filter(name__in = req['name'].split(','))
			elif req['email'] != '':
				details_list = detail.objects.filter(email__in = req['email'].split(','))
				owner_list = OwnerProfile.objects.filter(user__in = details_list)
				all_drivers = DriverProfile.objects.filter(owner__in = owner_list)
				print(details_list)

			data = {'drivers': all_drivers, 'staff': staff}
			if request.POST.get('unverify'):
				driver_id = request.POST.get('unverify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = False
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver unverified successfully')
				return redirect('admin_drivers')
			if request.POST.get('verify'):
				driver_id = request.POST.get('verify')
				driver = DriverProfile.objects.get(pk=driver_id)
				driver.is_verified = True
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver verified successfully')
				return redirect('admin_drivers')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_drivers.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_driver_edit(request, driver_id):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			driver = DriverProfile.objects.get(pk=driver_id)
			drform = driver_form(instance=driver)
			events = driver.events.all().order_by('-time')
			data = {'drform': drform, 'staff': staff, 'events':events}
			if request.POST.get('unverify'):
				driver.is_verified = False
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver unverified successfully')
				return redirect('admin_driver_edit', driver_id=driver.id)
			if request.POST.get('verify'):
				driver.is_verified = True
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver verified by ' + name
				)
				e.save()
				messages.success(request, 'Driver verified successfully')
				return redirect('admin_driver_edit', driver_id=driver.id)
			if request.POST.get('name'):
				driver.name = request.POST.get('name')
				driver.phone = request.POST.get('phone')
				picture = request.FILES.get('picture')
				if picture:
					driver.picture = picture
				driver.aadhar_card_number = request.POST.get('aadhar_card_number')
				aadhar_front_image = request.FILES.get('aadhar_front_image')
				if aadhar_front_image:
					driver.aadhar_front_image = aadhar_front_image
				aadhar_back_image = request.FILES.get('aadhar_front_image')
				if aadhar_back_image:
					driver.aadhar_back_image = aadhar_back_image
				driving_licence_front = request.FILES.get('driving_licence_front')
				if driving_licence_front:
					driver.driving_licence_front = driving_licence_front
				driving_licence_back = request.FILES.get('driving_licence_back')
				if driving_licence_back:
					driver.driving_licence_back = driving_licence_back
				driver.driving_licence_number = request.POST.get('driving_licence_number')
				driver.driving_licence_expiry_date = request.POST.get('driving_licence_expiry_date')
				driver.taxi_badge_number = request.POST.get('taxi_badge_number')
				driver.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					driver = driver,
					username = uname,
					email = email,
					text = 'Driver profile updated by ' + name
				)
				e.save()
				messages.success(request, 'Profile Updated Successfully')
				return redirect('admin_driver_edit', driver_id=driver.id)
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_driver_edit.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_cars(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			cars = Car.objects.all()
			data = {'cars':cars, 'staff':staff}
			if request.POST.get('unverify'):
				car_id = request.POST.get('unverify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = False
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Car unverified successfully')
				return redirect('admin_cars')
			if request.POST.get('verify'):
				car_id = request.POST.get('verify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = True
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car verified by ' + name
				)
				e.save()
				messages.success(request, 'Car verified successfully')
				return redirect('admin_cars')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_cars.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_verified_cars(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			cars = Car.objects.filter(is_verified=True)
			data = {'cars':cars, 'staff':staff, 'verified_cars':True}
			if request.POST.get('unverify'):
				car_id = request.POST.get('unverify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = False
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Car unverified successfully')
				return redirect('admin_verified_cars')
			if request.POST.get('verify'):
				car_id = request.POST.get('verify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = True
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car verified by ' + name
				)
				e.save()
				messages.success(request, 'Car verified successfully')
				return redirect('admin_verified_cars')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_cars.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_active_cars(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			owners = OwnerProfile.objects.filter(is_active = True)
			cars = Car.objects.filter(owner__in = owners)
			data = {'cars':cars, 'staff':staff, 'active_cars':True}
			if request.POST.get('unverify'):
				car_id = request.POST.get('unverify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = False
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Car unverified successfully')
				return redirect('admin_verified_cars')
			if request.POST.get('verify'):
				car_id = request.POST.get('verify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = True
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car verified by ' + name
				)
				e.save()
				messages.success(request, 'Car verified successfully')
				return redirect('admin_verified_cars')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_cars.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_inactive_cars(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			owners = OwnerProfile.objects.filter(is_active = False)
			cars = Car.objects.filter(owner__in = owners)
			data = {'cars':cars, 'staff':staff, 'inactive_cars':True}
			if request.POST.get('unverify'):
				car_id = request.POST.get('unverify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = False
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Car unverified successfully')
				return redirect('admin_verified_cars')
			if request.POST.get('verify'):
				car_id = request.POST.get('verify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = True
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car verified by ' + name
				)
				e.save()
				messages.success(request, 'Car verified successfully')
				return redirect('admin_verified_cars')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_cars.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_unverified_cars(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			cars = Car.objects.filter(is_verified=False)
			data = {'cars':cars, 'staff':staff,'unverified_cars':True}
			if request.POST.get('unverify'):
				car_id = request.POST.get('unverify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = False
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Car unverified successfully')
				return redirect('admin_unverified_cars')
			if request.POST.get('verify'):
				car_id = request.POST.get('verify')
				car = Car.objects.get(pk=car_id)
				car.is_verified = True
				car.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					car = car,
					username = uname,
					email = email,
					text = 'Car verified by ' + name
				)
				e.save()
				messages.success(request, 'Car verified successfully')
				return redirect('admin_unverified_cars')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_cars.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_car_edit(request, car_id):
    print(f'POST: {request.POST} FILES: {request.FILES}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        profile = CustomerProfile.objects.filter(user=details).first()
        user = request.user
        if owner:
            if owner.is_owner:
                return redirect('owner_dashboard')
            else:
                return redirect('vendor_dashboard')
        elif profile:
            return redirect('customer_dashboard')
        if details:
            if details.is_staff:
                staff = True
            else:
                staff = False
        else:
            staff = False
        if request.user.is_superuser or staff:
            car = Car.objects.get(pk=car_id)
            carform = car_form(instance=car)
            if request.POST.get('unverify'):
                car.is_verified = False
                car.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    car=car,
                    username=uname,
                    email=email,
                    text='Car un-verified by ' + name
                )
                e.save()
                messages.success(request, 'Car unverified successfully')
                return redirect('admin_car_edit', car_id=car.id)
            if request.POST.get('verify'):
                car.is_verified = True
                car.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    car=car,
                    username=uname,
                    email=email,
                    text='Car verified by ' + name
                )
                e.save()
                messages.success(request, 'Car verified successfully')
                return redirect('admin_car_edit', car_id=car.id)
            if request.POST.get('type'):
                car.type_id = request.POST.get('type')
                car.company_id = request.POST.get('company')
                car.name = request.POST.get('name')
                car.licence_plate_no = request.POST.get('licence_plate_no')
                rc_book_front = request.FILES.get('rc_book_front')
                if rc_book_front:
                    car.rc_book_front = rc_book_front
                rc_book_back = request.FILES.get('rc_book_back')
                if rc_book_back:
                    car.rc_book_back = rc_book_back
                car.rc_book_expiry_date = request.POST.get(
                    'rc_book_expiry_date')
                car.car_year = request.POST.get('car_year')
                car.owner_name = request.POST.get('owner_name')
                car.chassi_number = request.POST.get('chassi_number')
                car.insurance_no = request.POST.get('insurance_no')
                insurance_picture = request.FILES.get('insurance_picture')
                if insurance_picture:
                    car.insurance_picture = insurance_picture
                car.insurance_expiry_date = request.POST.get(
                    'insurance_expiry_date')
                car.insurance_company = request.POST.get('insurance_company')
                fitness_certificate = request.FILES.get('fitness_certificate')
                if fitness_certificate:
                    car.fitness_certificate = fitness_certificate
                car.fitness_expiry_date = request.POST.get(
                    'fitness_expiry_date')
                car_front = request.FILES.get('car_front')
                if car_front:
                    car.car_front = car_front
                car_back = request.FILES.get('car_back')
                if car_back:
                    car.car_back = car_back
                car_side_left = request.FILES.get('car_side_left')
                if car_side_left:
                    car.car_side_left = car_side_left
                car_side_right = request.FILES.get('car_side_right')
                if car_side_right:
                    car.car_side_right = car_side_right
                car_interior_front = request.FILES.get('car_interior_front')
                if car_interior_front:
                    car.car_interior_front = car_interior_front
                car_interior_back = request.FILES.get('car_interior_back')
                if car_interior_back:
                    car.car_interior_back = car_interior_back
                car_dickie = request.FILES.get('car_dickie')
                if car_dickie:
                    car.car_dickie = car_dickie
                car.save()
                uname = details.name if staff else 'admin'
                email = details.email if staff else user.email
                name = details.name if staff else user.email
                e = Event(
                    car=car,
                    username=uname,
                    email=email,
                    text='Car details updated by ' + name
                )
                e.save()
                messages.success(request, 'Car Edited Successfully')
                return redirect('admin_car_edit', car_id=car.id)
            events = car.events.all().order_by('-time')
            if staff:
                unseen_notifications = list(
                    details.notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    details.notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            else:
                unseen_notifications = list(
                    request.user.admin_notifications.filter(seen=False).order_by('-date'))
                all_notifications = list(
                    request.user.admin_notifications.all().order_by('-date'))
                unseen_count = len(unseen_notifications)
                if len(all_notifications) > 5:
                    while len(unseen_notifications) < 5:
                        unseen_notifications.append(all_notifications.pop(0))
                else:
                    unseen_notifications + all_notifications
            data = {'carform': carform, 'staff': staff, 'events': events,
                    'notify': unseen_notifications, 'unseen_count': unseen_count}
            return render(request, "admin_car_edit.html", data)
        else:
            return redirect('logout')
    else:
        return redirect('login_page')


def admin_customers(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_customers = CustomerProfile.objects.all()
			data = {'customers': all_customers, 'staff':staff}
			if request.POST.get('unverify'):
				customer_id = request.POST.get('unverify')
				customer = CustomerProfile.objects.get(pk=customer_id)
				customer.is_verified = False
				customer.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					customer = customer,
					username = uname,
					email = email,
					text = 'Customer un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Customer unverified successfully')
				return redirect('admin_customers')
			if request.POST.get('verify'):
				customer_id = request.POST.get('verify')
				customer = CustomerProfile.objects.get(pk=customer_id)
				customer.is_verified = True
				customer.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					customer = customer,
					username = uname,
					email = email,
					text = 'Customer verified by ' + name
				)
				e.save()
				messages.success(request, 'Customer verified successfully')
				return redirect('admin_customers')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify'] = unseen_notifications
			data['unseen_count'] =  unseen_count
			return render(request, "admin_customers.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_verified_customers(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_customers = CustomerProfile.objects.filter(is_verified=True)
			data = {'customers': all_customers, 'staff':staff, 'verified_customers':True}
			if request.POST.get('unverify'):
				customer_id = request.POST.get('unverify')
				customer = CustomerProfile.objects.get(pk=customer_id)
				customer.is_verified = False
				customer.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					customer = customer,
					username = uname,
					email = email,
					text = 'Customer un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Customer unverified successfully')
				return redirect('admin_verified_customers')
			if request.POST.get('verify'):
				customer_id = request.POST.get('verify')
				customer = CustomerProfile.objects.get(pk=customer_id)
				customer.is_verified = True
				customer.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					customer = customer,
					username = uname,
					email = email,
					text = 'Customer verified by ' + name
				)
				e.save()
				messages.success(request, 'Customer verified successfully')
				return redirect('admin_verified_customers')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify'] = unseen_notifications
			data['unseen_count'] =  unseen_count
			return render(request, "admin_customers.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_unverified_customers(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_customers = CustomerProfile.objects.filter(is_verified=False)
			data = {'customers': all_customers, 'staff':staff, 'unverified_customers':True}
			if request.POST.get('unverify'):
				customer_id = request.POST.get('unverify')
				customer = CustomerProfile.objects.get(pk=customer_id)
				customer.is_verified = False
				customer.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					customer = customer,
					username = uname,
					email = email,
					text = 'Customer un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Customer unverified successfully')
				return redirect('admin_unverified_customers')
			if request.POST.get('verify'):
				customer_id = request.POST.get('verify')
				customer = CustomerProfile.objects.get(pk=customer_id)
				customer.is_verified = True
				customer.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					customer = customer,
					username = uname,
					email = email,
					text = 'Customer verified by ' + name
				)
				e.save()
				messages.success(request, 'Customer verified successfully')
				return redirect('admin_unverified_customers')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify'] = unseen_notifications
			data['unseen_count'] =  unseen_count
			return render(request, "admin_customers.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = Trip.objects.all()
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				now = timezone.now()
				if (now > drop_time) and not trip.is_complete:
					show_complete = True
					print(trip.id)
				temp.append([trip, show_complete])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff}
			if request.POST.get('markcomplete'):
				trip_id = request.POST.get('markcomplete')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				vendor_amount = request.POST.get('vendor_amount')
				trip = Trip.objects.get(pk=trip_id)
				trip.vendor_amount = vendor_amount
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()
				threading.Thread(target=notification_for_trips, args = (trip,)).start()
				print("thresded created")
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify'] = unseen_notifications
			data['unseen_count'] = unseen_count
			return render(request, "admin_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_ongoing_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = Trip.objects.filter(is_complete=False, is_canceled=False, is_started = True).order_by('-pickup_date')
			temp = []
			for trip in all_trips:
				temp.append([trip,])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'ongoing_trips':True}
			print(f'DATA: {data}')
			if request.POST.get('start'):
				trip_id = request.POST.get('start')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_started = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip started by ' + name
				)
				e.save()
				messages.success(request, 'Trip started successfully')
				return redirect('admin_ongoing_trips')
			if request.POST.get('markcomplete'):
				trip_id = request.POST.get('markcomplete')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_ongoing_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_ongoing_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()

				threading.Thread(target=notification_for_trips, args = (trip,)).start()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_ongoing_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_upcoming_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = Trip.objects.filter(is_complete=False, is_canceled=False, is_started=False).order_by('-pickup_date')
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
					print(trip.id)
				show_start = False
				pickup_time = datetime.datetime.combine(trip.pickup_date, trip.pickup_time)
				if (datetime.datetime.now() > pickup_time) and not trip.is_started:
					show_start = True
				temp.append([trip, show_complete, show_start])
				print(f'TRIP: {trip} \nPICKUP_TIME: {pickup_time} \nNOW: {datetime.datetime.now()} \nSHOW_START: {show_start} \nDROP_TIME: {drop_time} \nSHOW_COMPLETE: {show_complete}')
			print(f'TEMP: {temp}')
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'upcoming_trips':True}
			print(f'DATA: {data}')
			if request.POST.get('start'):
				trip_id = request.POST.get('start')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_started = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip started by ' + name
				)
				e.save()
				messages.success(request, 'Trip started successfully')
				return redirect('admin_upcoming_trips')
			if request.POST.get('markcomplete'):
				trip_id = request.POST.get('markcomplete')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_upcoming_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_upcoming_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()

				threading.Thread(target=notification_for_trips, args = (trip,)).start()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_upcoming_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

# def admin_verified_trips(request):
# 	print(f'POST: {request.POST} FILES: {request.FILES}')
# 	if request.user.is_authenticated:
# 		details = detail.objects.filter(email=request.user.email).first()
# 		owner = OwnerProfile.objects.filter(user=details).first()
# 		profile = CustomerProfile.objects.filter(user=details).first()
# 		user = request.user
# 		if owner:
# 			if owner.is_owner:
# 				return redirect('owner_dashboard')
# 			else:
# 				return redirect('vendor_dashboard')
# 		elif profile:
# 			return redirect('customer_dashboard')
# 		if details:
# 			if details.is_staff:
# 				staff = True
# 			else:
# 				staff = False
# 		else:
# 			staff = False
# 		if request.user.is_superuser or staff:
# 			all_trips = Trip.objects.filter(is_verified = True).order_by('-pickup_date')
# 			data = {'trips': all_trips, 'staff':staff, 'verified_trips':True}
# 			print(f'DATA: {data}')
# 			if request.POST.get('start'):
# 				trip_id = request.POST.get('start')
# 				trip = Trip.objects.get(pk=trip_id)
# 				trip.is_started = True
# 				trip.save()
# 				uname = details.name if staff else 'admin'
# 				email = details.email if staff else user.email
# 				name =  details.name if staff else user.email
# 				e = Event(
# 					trip = trip,
# 					username = uname,
# 					email = email,
# 					text = 'Trip started by ' + name
# 				)
# 				e.save()
# 				messages.success(request, 'Trip started successfully')
# 				return redirect('admin_verified_trips')
# 			if request.POST.get('markcomplete'):
# 				trip_id = request.POST.get('markcomplete')
# 				trip = Trip.objects.get(pk=trip_id)
# 				trip.is_complete = True
# 				trip.save()
# 				uname = details.name if staff else 'admin'
# 				email = details.email if staff else user.email
# 				name =  details.name if staff else user.email
# 				e = Event(
# 					trip = trip,
# 					username = uname,
# 					email = email,
# 					text = 'Trip un-verified by ' + name
# 				)
# 				e.save()
# 				messages.success(request, 'Trip completed successfully')
# 				return redirect('admin_verified_trips')
# 			if request.POST.get('unverify'):
# 				trip_id = request.POST.get('unverify')
# 				trip = Trip.objects.get(pk=trip_id)
# 				trip.is_verified = False
# 				trip.save()
# 				uname = details.name if staff else 'admin'
# 				email = details.email if staff else user.email
# 				name =  details.name if staff else user.email
# 				e = Event(
# 					trip = trip,
# 					username = uname,
# 					email = email,
# 					text = 'Trip un-verified by ' + name
# 				)
# 				e.save()
# 				messages.success(request, 'Trip unverified successfully')
# 				return redirect('admin_verified_trips')
# 			if request.POST.get('verify'):
# 				trip_id = request.POST.get('verify')
# 				trip = Trip.objects.get(pk=trip_id)
# 				trip.is_verified = True
# 				trip.save()
# 				uname = details.name if staff else 'admin'
# 				email = details.email if staff else user.email
# 				name =  details.name if staff else user.email
# 				e = Event(
# 					trip = trip,
# 					username = uname,
# 					email = email,
# 					text = 'Trip verified by ' + name
# 				)
# 				e.save()

# 				threading.Thread(target=notification_for_trips, args = (trip,)).start()
# 				messages.success(request, 'Trip verified successfully')
# 				return redirect('admin_verified_trips')
# 			print(f'DATA: {data}')
# 			if staff:
# 				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
# 				all_notifications = list(details.notifications.all().order_by('-date'))
# 				unseen_count = len(unseen_notifications)
# 				if len(all_notifications) > 5:
# 					while len(unseen_notifications) < 5:
# 						unseen_notifications.append(all_notifications.pop(0))
# 				else:
# 					unseen_notifications + all_notifications
# 			else:
# 				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
# 				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
# 				unseen_count = len(unseen_notifications)
# 				if len(all_notifications) > 5:
# 					while len(unseen_notifications) < 5:
# 						unseen_notifications.append(all_notifications.pop(0))
# 				else:
# 					unseen_notifications + all_notifications
# 			data['notify']=unseen_notifications
# 			data['unseen_count']= unseen_count
# 			return render(request, "admin_trips.html", data)
# 		else:
# 			return redirect('logout')
# 	else:
# 		return redirect('login_page')

def admin_verified_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = Trip.objects.filter(is_verified=True).order_by('-pickup_date')
			temp = []
			for trip in all_trips:
				temp.append([trip,])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'verified_trips':True}
			print(f'DATA: {data}')
			if request.POST.get('start'):
				trip_id = request.POST.get('start')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_started = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip started by ' + name
				)
				e.save()
				messages.success(request, 'Trip started successfully')
				return redirect('admin_verified_trips')
			if request.POST.get('markcomplete'):
				trip_id = request.POST.get('markcomplete')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_verified_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_verified_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()

				threading.Thread(target=notification_for_trips, args = (trip,)).start()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_verified_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_unverified_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = Trip.objects.filter(is_verified=False).order_by('-pickup_date')
			temp = []
			for trip in all_trips:
				temp.append([trip,])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'unverified_trips':True}
			print(f'DATA: {data}')
			if request.POST.get('start'):
				trip_id = request.POST.get('start')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_started = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip started by ' + name
				)
				e.save()
				messages.success(request, 'Trip started successfully')
				return redirect('admin_unverified_trips')
			if request.POST.get('markcomplete'):
				trip_id = request.POST.get('markcomplete')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_unverified_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_unverified_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()

				threading.Thread(target=notification_for_trips, args = (trip,)).start()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_unverified_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_active_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = Trip.objects.filter(is_complete=False, is_canceled=False).order_by('-pickup_date')
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
					print(trip.id)
				show_start = False
				pickup_time = datetime.datetime.combine(trip.pickup_date, trip.pickup_time)
				if (datetime.datetime.now() > pickup_time) and not trip.is_started:
					show_start = True
				temp.append([trip, show_complete, show_start])
				print(f'TRIP: {trip} \nPICKUP_TIME: {pickup_time} \nNOW: {datetime.datetime.now()} \nSHOW_START: {show_start} \nDROP_TIME: {drop_time} \nSHOW_COMPLETE: {show_complete}')
			print(f'TEMP: {temp}')
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'active_trips':True}
			print(f'DATA: {data}')
			if request.POST.get('start'):
				trip_id = request.POST.get('start')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_started = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip started by ' + name
				)
				e.save()
				messages.success(request, 'Trip started successfully')
				return redirect('admin_active_trips')
			if request.POST.get('markcomplete'):
				trip_id = request.POST.get('markcomplete')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_active_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_active_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()

				threading.Thread(target=notification_for_trips, args = (trip,)).start()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_active_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_completed_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = Trip.objects.filter(is_complete=True, is_canceled=False)
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
					print(trip.id)
				temp.append([trip, show_complete])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'completed_trips':True}
			if request.POST.get('markcomplete'):
				trip_id = request.POST.get('markcomplete')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_completed_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_completed_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_completed_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_canceled_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = Trip.objects.filter(is_canceled=True)
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
					print(trip.id)
				temp.append([trip, show_complete])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'canceled_trips':True}
			if request.POST.get('markcomplete'):
				trip_id = request.POST.get('markcomplete')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_canceled_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_canceled_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_canceled_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_trip_by_location(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			req = request.POST
			if req['pickup_city'] != '':
				print(req['pickup_city'].split(','))
				all_trips = Trip.objects.filter(pickup_city__in = req['city'].split(',')).order_by('-pickup_date')
			elif req['pickup_state'] != '':
				print(req['pickup_state'].split(','))
				all_trips = Trip.objects.filter(pickup_state__in = req['pickup_state'].split(',')).order_by('-pickup_date')
			if req['drop_city'] != '':
				print(req['drop_city'].split(','))
				all_trips = Trip.objects.filter(drop_city__in = req['city'].split(',')).order_by('-pickup_date')
			elif req['drop_state'] != '':
				print(req['drop_state'].split(','))
				all_trips = Trip.objects.filter(drop_state__in = req['drop_state'].split(',')).order_by('-pickup_date')
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
					print(trip.id)
				temp.append([trip, show_complete])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'canceled_trips':True}
			if request.POST.get('markcomplete'):
				trip_id = request.POST.get('markcomplete')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_canceled_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_canceled_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = Trip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_canceled_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_vendor_canceled_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = VendorTrip.objects.filter(is_canceled=True)
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
				temp.append([trip,show_complete])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'canceled_trips':True}
			if request.POST.get('markcompletevendor'):
				trip_id = request.POST.get('markcompletevendor')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				print(trip.id)
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip completed by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_vendor_canceled_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_vendor_canceled_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_vendor_canceled_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_vendor_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_vendor_demo_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = VendorTrip.objects.filter(is_demo=True)
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
				temp.append([trip,show_complete])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'demo':True}
			if request.POST.get('markcompletevendor'):
				trip_id = request.POST.get('markcompletevendor')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				print(trip.id)
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip completed by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_vendor_demo_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_vendor_demo_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_vendor_demo_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_vendor_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_vendor_completed_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = VendorTrip.objects.filter(is_complete=True)
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
				temp.append([trip,show_complete])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'completed_trip':True}
			if request.POST.get('markcompletevendor'):
				trip_id = request.POST.get('markcompletevendor')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				print(trip.id)
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip completed by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_vendor_demo_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_vendor_demo_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_vendor_demo_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_vendor_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_vendor_posted_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = VendorTrip.objects.filter(poster__isnull=True)
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
				temp.append([trip,show_complete])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff, 'posted_trips':True}
			if request.POST.get('markcompletevendor'):
				trip_id = request.POST.get('markcompletevendor')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				print(trip.id)
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip completed by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_vendor_posted_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_vendor_posted_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_vendor_posted_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_vendor_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_trip_view(request, trip_id):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			trip = Trip.objects.get(pk=trip_id)
			events = trip.events.all().order_by('-time')
			oform = admin_owner_form()
			dform = admin_driver_form()
			# EDIT TRIP DATA
			trip_type = 'round' if trip.round_trip else 'oneway'
			distance = trip.distance
			days = trip.days
			tinfo = trip.traveller.first()
			print(tinfo)
			trform = traveller_form(instance=tinfo)
			# CAR TYPE DATA
			# car_types = CarType.objects.filter(is_active=True)
			if trip.round_trip:
				car_types = CarType.objects.filter(is_active=True).order_by('local_round_min_charge')
			else:
				car_types = CarType.objects.filter(is_active=True).order_by('local_oneway_min_charge')
			type_data = []
			if trip_type == "round":
				for type in car_types:
					round_distance = int(distance) * 2
					days = int(days)
					temp_dist = round_distance - type.local_round_min_km
					day_dist = type.local_round_min_km * days
					if round_distance < day_dist:
						day_based = True
						extra_dist_charges = 0
						day_charges = type.local_round_min_charge * days
						charges = int(day_charges)
					else:
						day_based = False
						day_charges = False
						if temp_dist > 0:
							extra_dist_charges = type.local_round_rate_per_km * temp_dist
							charges = type.local_round_min_charge + extra_dist_charges
							charges = charges
						else:
							extra_dist_charges = 0
							charges = type.local_round_min_charge
							charges = charges
					# Driver allowance
					total_driver_allowance = type.local_round_driver_allowance * days
					charges += total_driver_allowance
					charges -= type.redeem_wallet_amount
					charges_before_tax = int(charges)
					tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
					charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100)) 
					final_charges = int( charges )
					if day_based:
						type.local_round_min_charge = int(day_charges)
					else:
						type.local_round_min_charge = int(charges)
					type.local_round_min_km = int(round_distance)
					type_data.append([type, charges])
			if trip_type == "oneway":	
				for type in car_types:
					temp_dist = distance - type.local_oneway_min_km 
					# If distance is more than minumum distance
					if temp_dist > 0:
						extra_dist_charges = type.local_oneway_rate_per_km*temp_dist
						charges = type.local_oneway_min_charge + extra_dist_charges
					else:
						extra_dist_charges = 0
						charges = type.local_oneway_min_charge
					tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
					total_driver_allowance = 0
					charges -= type.redeem_wallet_amount
					charges_before_tax = charges
					charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
					charges = int(charges)
					final_charges = charges
					type.local_oneway_min_km = int(distance)
					type.local_oneway_min_charge = int(charges)
					type_data.append([type, charges])
			owners = OwnerProfile.objects.filter(is_vendor=False, is_verified=True)
			tempdrivers = DriverProfile.objects.filter(owner__in = owners)
			drivers = []
			for driver in tempdrivers:
				car = driver.owner.cars.first()
				car_name = car.name
				car_licence = car.licence_plate_no
				drivers.append([driver, car_name, car_licence])
			vendors = OwnerProfile.objects.filter(is_vendor=True, is_verified=True)
			data = {
				'trip': trip, 
				'staff': staff, 
				'events':events, 
				'car_types':type_data, 
				'trform':trform,
				'drivers':drivers,
				'vendors':vendors,
				}
			if request.POST.get('action') == 'get_vendor_drivers':
				vendor_id = request.POST.get('vendor_id')
				vendor = OwnerProfile.objects.get(pk=vendor_id)
				drivers = vendor.drivers.all() 
				cars = vendor.cars.all()
				data = {'drivers': [], 'cars':[]}
				for driver in drivers:
					data['drivers'].append([driver.id, driver.name + '-' + driver.phone])
				for car in cars:
					data['cars'].append([car.id, car.name + '-' + car.licence_plate_no])
				return JsonResponse(data)
			if request.POST.get('assign_driver'):
				driver_id = request.POST.get('owner_driver')
				driver = DriverProfile.objects.get(pk=driver_id)
				owner = driver.owner
				car = owner.cars.first()
				trip.owner = owner
				trip.driver = driver
				trip.car = car
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Driver assigned by ' + uname
				)
				e.save()
				messages.success(request, 'Driver assigned successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('assign_vendor'):
				owner_id = request.POST.get('vendor')
				driver_id = request.POST.get('vendor_driver')
				car_id = request.POST.get('vendor_car')
				owner = OwnerProfile.objects.get(pk=owner_id)
				driver = DriverProfile.objects.get(pk=owner_id)
				car = Car.objects.get(pk=car_id)
				trip.owner = owner
				trip.driver = driver
				trip.car = car
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Owner and driver assigned by ' + uname
				)
				e.save()
				messages.success(request, 'Driver and owner assigned successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('unverify'):
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + uname
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('verify'):
				vendor_amount = request.POST.get('vendor_amount')
				trip.vendor_amount = vendor_amount
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + uname
				)
				e.save()
				threading.Thread(target=notification_for_trips, args = (trip,)).start()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('makevisible'):
				trip.driver_is_visible = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Driver details made visible by ' + uname
				)
				e.save()
				messages.success(request, 'Driver is visible to customer')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('hidedriver'):
				trip.driver_is_visible = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Driver details made hidden by ' + uname
				)
				e.save()
				messages.success(request, 'Driver is not visible to customer')
			if request.POST.get('makevisibletraveller'):
				trip.traveller_is_visible = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Traveller details made visible by ' + uname
				)
				e.save()
				messages.success(request, 'Traveller is visible to vendor')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('hidetraveller'):
				trip.traveller_is_visible = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Traveller details made hidden by ' + uname
				)
				e.save()
				messages.success(request, 'Traveller is not visible to vendor')
			if request.POST.get('delete'):
				trip.delete()
				messages.success(request, 'Trip deleted successfully')
				return redirect('admin_trips')
			if request.POST.get('cancel'):
				trip.is_canceled = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip cancelled by ' + uname
				)
				e.save()
				messages.success(request, 'Trip canceled successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('uncancel'):
				trip.is_canceled = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-cancelled by ' + uname
				)
				e.save()
				messages.success(request, 'Trip un-canceled successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			# EDIT TRIP POSTS
			if request.POST.get('time'):
				trip.pickup_time = request.POST.get('time')
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip details updated by ' + uname
				)
				e.save()
				messages.success(request, 'Pickup time updated successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('toll'):
				old_toll = trip.toll_charges
				
				new_toll = int(request.POST.get('toll'))
				trip.toll_charges = request.POST.get('toll')
				trip.bill_amount = trip.bill_amount - old_toll + new_toll
				print(trip.bill_amount)
				trip.save()
				print(trip.bill_amount)
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip details updated by ' + uname
				)
				e.save()
				messages.success(request, 'Pickup time updated successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('date'):
				trip.pickup_date = request.POST.get('date')
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip details updated by ' + uname
				)
				e.save()
				messages.success(request, 'Pickup date updated successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('car_type'):
				car_type_id = request.POST.get('car_type')
				car_type = CarType.objects.get(pk=car_type_id)
				final_charges = 0
				trip_perimeter = request.GET.get('trip_perimeter')
				if trip_perimeter == 'local':
					if time_frame == "morning":
						surge_charge = distance*car_type.local_morning_surge_charge
					elif time_frame == "evening":
						surge_charge = distance*car_type.local_evening_surge_charge
					elif time_frame == "night":
						surge_charge = distance*car_type.local_night_surge_charge
					surge_charge = surge_charge + trip.toll_charges + car_type.permit
					if trip_type == 'oneway':
						temp_dist = distance - car_type.local_oneway_min_km 
						
						# If distance is more than minumum distance
						if temp_dist > 0:
							extra_dist_charges = car_type.local_oneway_rate_per_km*temp_dist
							charges = car_type.local_oneway_min_charge + extra_dist_charges + surge_charge
						else:
							extra_dist_charges = 0
							charges = car_type.local_oneway_min_charge
						tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
						day_based = False
						day_charges = False
						total_driver_allowance = 0
						charges -= car_type.redeem_wallet_amount
						charges_before_tax = charges
						charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
						charges = int(charges)
						final_charges = charges	
					if trip_type == 'round':
						distance = int(distance) * 2
						days = int(days)
						temp_dist = distance - car_type.local_round_min_km
						
						day_dist = car_type.local_round_min_km * days
						if distance < day_dist:
							day_based = True
							extra_dist_charges = 0
							day_charges = car_type.local_round_min_charge * days
							charges = int(day_charges)
						else:
							day_based = False
							day_charges = False
							if temp_dist > 0:
								extra_dist_charges = car_type.local_round_rate_per_km * temp_dist
								charges = car_type.local_round_min_charge + extra_dist_charges + surge_charge
								charges = charges
							else:
								extra_dist_charges = 0
								charges = car_type.local_round_min_charge
								charges = charges
						# Driver allowance
						total_driver_allowance = car_type.local_round_driver_allowance * days
						charges += total_driver_allowance
						charges -= car_type.redeem_wallet_amount
						charges_before_tax = int(charges)
						tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
						charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100)) 
						final_charges = int( charges )
				if trip_perimeter == 'outstation':
					if time_frame == "morning":
						surge_charge = distance*car_type.outstation_morning_surge_charge
					elif time_frame == "evening":
						surge_charge = distance*car_type.outstation_evening_surge_charge
					elif time_frame == "night":
						surge_charge = distance*car_type.outstation_night_surge_charge
					surge_charge = surge_charge + trip.toll_charges + car_type.permit
					if trip_type == 'oneway':
						temp_dist = distance - car_type.outstation_oneway_min_km 
						
						# If distance is more than minumum distance
						if temp_dist > 0:
							extra_dist_charges = car_type.outstation_oneway_rate_per_km*temp_dist
							charges = car_type.outstation_oneway_min_charge + extra_dist_charges + surge_charge + car_type.oustation_oneway_stay_charge
						else:
							extra_dist_charges = 0
							charges = car_type.outstation_oneway_min_charge + car_type.oustation_oneway_stay_charge
						tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
						day_based = False
						day_charges = False
						total_driver_allowance = 0
						charges -= car_type.redeem_wallet_amount
						charges_before_tax = charges
						charges = charges_before_tax + int(int(charges_before_tax * tax_percent/100))
						charges = int(charges)
						final_charges = charges	
					if trip_type == 'round':
						distance = int(distance) * 2
						days = int(days)
						temp_dist = distance - car_type.outstation_round_min_km
						
						day_dist = car_type.outstation_round_min_km * days
						if distance < day_dist:
							day_based = True
							extra_dist_charges = 0
							day_charges = car_type.outstation_round_min_charge * days
							charges = int(day_charges)
						else:
							day_based = False
							day_charges = False
							if temp_dist > 0:
								extra_dist_charges = car_type.outstation_round_rate_per_km * temp_dist
								charges = car_type.outstation_round_min_charge + extra_dist_charges + surge_charge
								charges = charges
							else:
								extra_dist_charges = 0
								charges = car_type.outstation_round_min_charge
								charges = charges
						# Driver allowance
						total_driver_allowance = car_type.outstation_round_driver_allowance * days
						charges += total_driver_allowance
						charges -= car_type.redeem_wallet_amount
						charges_before_tax = int(charges)
						tax_percent = Tax.objects.first().GST if Tax.objects.first() else 5
						charges = charges_before_tax + int(charges_before_tax * tax_percent/100) 
						final_charges = int( charges )
				trip.bill_amount = final_charges
				trip.fare = int(charges_before_tax)
				trip.tax = int(charges_before_tax * tax_percent/100)
				trip.day_charges = day_charges
				trip.extra_dist_charges = int(extra_dist_charges)
				trip.total_driver_allowance = total_driver_allowance
				trip.tax_percent = tax_percent
				trip.car_type = car_type
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					trip = trip,
					username = uname,
					email = email,
					text = 'Trip details updated by ' + uname
				)
				e.save()
				messages.success(request, 'Car type updated successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			if request.POST.get('traveller_edit'):
				tinfo = trip.traveller.first()
				trform = traveller_form(request.POST,instance=tinfo)
				if trform.is_valid():
					trform.save()
					uname = details.name if staff else 'admin'
					email = details.email if staff else user.email
					name =  details.name if staff else user.email
					e = Event(
						trip = trip,
						username = uname,
						email = email,
						text = 'Traveller form updated by ' + uname
					)
					e.save()
				else:
					print(f'ERRROR: {trform.errors}')
					messages.error(request, 'Error: Please enter valid data')
					return redirect('admin_trip_view', trip_id=trip.id)
				messages.success(request, 'Traveller information updated successfully')
				return redirect('admin_trip_view', trip_id=trip.id)
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_trip_view.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def admin_post_trip(request):
	print(f'THIS IS POST: {request.POST}')
	print(f'THIS IS GET: {request.GET}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		# Confirm Booking 
		if request.POST.get('confirm_without_traveller'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('car_type')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			days = request.GET.get('days')
			vendor_amount = request.GET.get('vendor_amount')
			demo = True if request.POST.get('demo')=='on' else False
			if days == 'None':
				days = 0
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('admin_trips')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			total_time = time + 2.0
			pickup_temp_date = datetime.datetime.strptime(pickup_date, '%Y-%m-%d')
			pickup_temp_time = datetime.datetime.strptime(pickup_time, '%H:%M').time()
			pickup_datetime = datetime.datetime.combine(pickup_temp_date, pickup_temp_time)
			drop_datetime = pickup_datetime + datetime.timedelta(days=int(days), hours=total_time)
			print(f'ptd: {pickup_temp_date} ptt: {pickup_temp_time} pdatetime: {pickup_datetime} drop_datetime: {drop_datetime}')
			car_type = CarType.objects.get(pk=car_type_id)
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			# New Trip generation
			trip = VendorTrip()
			trip.pickup_city = pickup_city
			trip.pickup_state = pickup_state
			trip.drop_city = drop_city
			trip.drop_state = drop_state
			trip.customer = profile
			trip.pickup_date = pickup_date
			trip.pickup_time = pickup_time
			trip.drop_time = drop_datetime
			trip.car_type = car_type
			trip.is_demo = demo
			print(f'PICKUP CORDS: {pickup_cordinates} DROP CORDS: {drop_cordinates}')
			trip.pickup_location = pickup_cordinates
			trip.drop_location = drop_cordinates
			trip.pickup_address = pickup_address
			trip.drop_address = drop_address
			if trip_type == 'round':
				trip.round_trip = True
				trip.days = days
			trip.vendor_amount = vendor_amount
			trip.distance = distance
			trip.poster =	None
			trip.is_verified = True
			trip.save()
			tdate = trip.pickup_date
			tdate = tdate.replace('-','')	
			ttime = trip.pickup_time
			ttime = ttime.replace(':','')
			trip_no_str = tdate + ttime + '000000'
			trip_no_str = str(int(trip_no_str) + int(trip.id))
			trip.trip_no = trip_no_str
			trip.save()
			print(f'AFTER SAVE PICKUP CORDS: {trip.pickup_location} DROP CORDS: {trip.drop_location}')
			uname = details.name if staff else 'admin'
			email = details.email if staff else user.email
			name =  details.name if staff else user.email
			e = Event(
				vendor_trip = trip,
				username = uname,
				email = email,
				text = 'Trip created by ' + uname
			)
			e.save()
			messages.success(request, 'Trip created successfully')
			return redirect('admin_trips')
		if request.POST.get('confirm_booking'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('car_type')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			days = request.GET.get('days')
			vendor_amount = request.GET.get('vendor_amount')
			demo = True if request.GET.get('demo') else False
			if days == 'None':
				days = 0
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('admin_trips')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			total_time = time + 2.0
			pickup_temp_date = datetime.datetime.strptime(pickup_date, '%Y-%m-%d')
			pickup_temp_time = datetime.datetime.strptime(pickup_time, '%H:%M').time()
			pickup_datetime = datetime.datetime.combine(pickup_temp_date, pickup_temp_time)
			drop_datetime = pickup_datetime + datetime.timedelta(days=int(days), hours=total_time)
			print(f'ptd: {pickup_temp_date} ptt: {pickup_temp_time} pdatetime: {pickup_datetime} drop_datetime: {drop_datetime}')
			car_type = CarType.objects.get(pk=car_type_id)
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			pickup_city, pickup_state = get_state_and_city(pickup_address)
			drop_city, drop_state = get_state_and_city(drop_address)
			# New Trip generation
			trip = VendorTrip()
			trip.pickup_city = pickup_city
			trip.pickup_state = pickup_state
			trip.drop_city = drop_city
			trip.drop_state = drop_state
			trip.customer = profile
			trip.pickup_date = pickup_date
			trip.pickup_time = pickup_time
			trip.drop_time = drop_datetime
			trip.car_type = car_type
			print(f'PICKUP CORDS: {pickup_cordinates} DROP CORDS: {drop_cordinates}')
			trip.pickup_location = pickup_cordinates
			trip.drop_location = drop_cordinates
			trip.pickup_address = pickup_address
			trip.drop_address = drop_address
			if trip_type == 'round':
				trip.round_trip = True
				trip.days = days
			trip.vendor_amount = vendor_amount
			trip.distance = distance
			trip.poster = owner
			trip.is_verified = True
			trip.save()
			tdate = trip.pickup_date
			tdate = tdate.replace('-','')	
			ttime = trip.pickup_time
			ttime = ttime.replace(':','')
			trip_no_str = tdate + ttime + '000000'
			trip_no_str = str(int(trip_no_str) + int(trip.id))
			trip.trip_no = trip_no_str
			trip.save()
			print(f'AFTER SAVE PICKUP CORDS: {trip.pickup_location} DROP CORDS: {trip.drop_location}')
			e = Event(
				vendor_trip = trip,
				username = owner.user.name,
				email = owner.user.email,
				text = 'Trip created by ' + owner.user.name 
			)
			e.save()
			# Travellers Object
			traveller = TravellersInformation()
			traveller.vendor_trip = trip
			traveller.name = request.POST.get('name')
			traveller.phone = request.POST.get('phone')
			traveller.email = request.POST.get('email')
			traveller.address = request.POST.get('address')
			traveller.no_of_travellers = request.POST.get('no_of_travellers')
			traveller.no_of_bags = request.POST.get('no_of_bags')
			traveller.special_instructions = request.POST.get('special_instructions')
			carrier = False
			if request.POST.get('carrier_required') == 'on':
				carrier = True
			traveller.carrier_required = carrier
			traveller.save()
			return redirect('admin_trips')
		# Pick up location
		if request.GET.get('pickup_location'):
			pickup_location = request.GET.get('pickup_location')
			trip_type = request.GET.get('trip_type')
			days = request.GET.get('days')
			drop_location = request.GET.get('drop_location')
			trip_perimeter = request.GET.get('trip_perimeter')
			if not drop_location:
				tform = trip_drop(initial={'pickup_location':pickup_location})
				data = {'tform':tform,'trip_type':trip_type, 'days':days, 'trip_perimeter':trip_perimeter}
				return render(request, 'admin_create_trip.html', data)
		# Drop Location
		if request.GET.get('drop_location'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type = request.GET.get('car_type')
			trip_type = request.GET.get('trip_type')
			days = request.GET.get('days')
			if not car_type:
				if not(pickup_location and drop_location):
					messages.error(request, 'Please enter valid details')
					return redirect('admin_trips')
				pickup_cordinates = pickup_location.split(',')
				drop_cordinates = drop_location.split(',')
				pickup_cordinates.reverse()
				drop_cordinates.reverse()
				distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
				if not distance:
					messages.error(request, 'Please select valid locations')
					return redirect('admin_trips')
				car_types = CarType.objects.filter(is_active=True)
				pickup_address = get_location_address(pickup_cordinates)
				drop_address = get_location_address(drop_cordinates)
				data = {
					'pickup_address':pickup_address,
					'drop_address':drop_address, 
					'car_types': car_types, 
					'pickup_location': pickup_location, 
					'drop_location': drop_location,
					'trip_type': trip_type,
					'days': days
					}
				return render(request, 'admin_select_cars.html', data)
		# Select time and car type
		if request.GET.get('car_type'):
			pickup_location = request.GET.get('pickup_location')
			drop_location = request.GET.get('drop_location')
			car_type_id = request.GET.get('car_type')
			pickup_time = request.GET.get('pickup_time')
			pickup_date = request.GET.get('pickup_date')
			vendor_amount = request.GET.get('vendor_amount')
			days = request.GET.get('days')
			trip_type = request.GET.get('trip_type')
			if not(pickup_location and drop_location and car_type_id and pickup_time and pickup_date):
				messages.error(request, 'Please enter valid details')
				return redirect('vendor_post_trip')
			pickup_cordinates = pickup_location.split(',')
			drop_cordinates = drop_location.split(',')
			pickup_cordinates.reverse()
			drop_cordinates.reverse()
			# Recalculate based on coordinates
			distance, time = get_distance_and_time(pickup_cordinates, drop_cordinates)
			car_type = CarType.objects.get(pk=car_type_id)
			pickup_address = get_location_address(pickup_cordinates)
			drop_address = get_location_address(drop_cordinates)
			trform = traveller_form()
			data = {
				'vendor_amount':vendor_amount,
				'pickup_address':pickup_address,
				'drop_address':drop_address, 
				'pickup_location':pickup_location, 
				'pickup_time': pickup_time,
				'pickup_date': pickup_date,
				'drop_location':drop_location, 
				'trform': trform, 
				'distance': distance,
				'trip_type': trip_type,
				'days': days,
				'car_type':car_type,
				'distance': round(distance, 2)
				}
			return render(request, 'admin_confirm_booking.html', data)
		tform = trip_pickup()
		data = {'tform':tform}
		if staff:
			unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
			all_notifications = list(details.notifications.all().order_by('-date'))
			unseen_count = len(unseen_notifications)
			if len(all_notifications) > 5:
				while len(unseen_notifications) < 5:
					unseen_notifications.append(all_notifications.pop(0))
			else:
				unseen_notifications + all_notifications
		else:
			unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
			all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
			unseen_count = len(unseen_notifications)
			if len(all_notifications) > 5:
				while len(unseen_notifications) < 5:
					unseen_notifications.append(all_notifications.pop(0))
			else:
				unseen_notifications + all_notifications
		data['notify']=unseen_notifications
		data['unseen_count']= unseen_count
		return render(request, 'admin_create_trip.html', data)
	else:
		return redirect('login_page')

def admin_vendor_trips(request):
	print(f'POST: {request.POST} FILES: {request.FILES}')
	if request.user.is_authenticated:
		details = detail.objects.filter(email=request.user.email).first()
		owner = OwnerProfile.objects.filter(user=details).first()
		profile = CustomerProfile.objects.filter(user=details).first()
		user = request.user
		if owner:
			if owner.is_owner:
				return redirect('owner_dashboard')
			else:
				return redirect('vendor_dashboard')
		elif profile:
			return redirect('customer_dashboard')
		if details:
			if details.is_staff:
				staff = True
			else:
				staff = False
		else:
			staff = False
		if request.user.is_superuser or staff:
			all_trips = VendorTrip.objects.all()
			temp = []
			for trip in all_trips:
				show_complete = False
				drop_time = trip.drop_time + timedelta(hours=2)
				if (datetime.datetime.now() > drop_time) and not trip.is_complete:
					show_complete = True
				temp.append([trip,show_complete])
			all_trips = temp
			data = {'trips': all_trips, 'staff':staff}
			if request.POST.get('markcompletevendor'):
				trip_id = request.POST.get('markcompletevendor')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_complete = True
				trip.save()
				print(trip.id)
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip completed by ' + name
				)
				e.save()
				messages.success(request, 'Trip completed successfully')
				return redirect('admin_vendor_trips')
			if request.POST.get('unverify'):
				trip_id = request.POST.get('unverify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = False
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip un-verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip unverified successfully')
				return redirect('admin_vendor_trips')
			if request.POST.get('verify'):
				trip_id = request.POST.get('verify')
				trip = VendorTrip.objects.get(pk=trip_id)
				trip.is_verified = True
				trip.save()
				uname = details.name if staff else 'admin'
				email = details.email if staff else user.email
				name =  details.name if staff else user.email
				e = Event(
					vendor_trip = trip,
					username = uname,
					email = email,
					text = 'Trip verified by ' + name
				)
				e.save()
				messages.success(request, 'Trip verified successfully')
				return redirect('admin_vendor_trips')
			print(f'DATA: {data}')
			if staff:
				unseen_notifications = list(details.notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(details.notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			else:
				unseen_notifications = list(request.user.admin_notifications.filter(seen=False).order_by('-date'))
				all_notifications = list(request.user.admin_notifications.all().order_by('-date'))
				unseen_count = len(unseen_notifications)
				if len(all_notifications) > 5:
					while len(unseen_notifications) < 5:
						unseen_notifications.append(all_notifications.pop(0))
				else:
					unseen_notifications + all_notifications
			data['notify']=unseen_notifications
			data['unseen_count']= unseen_count
			return render(request, "admin_vendor_trips.html", data)
		else:
			return redirect('logout')
	else:
		return redirect('login_page')

def ajax_vehical_filter(request):
    group = 'car'
    if request.GET.get('group') is not None:
        group = request.GET.get('group')
        # print(group)
    type = request.GET.get('type')
    # print(type)
    company = request.GET.get('company')
    # print(company)
    query = Q(group=group)
    if type:
        query = query & Q(type=type)
    if company:
        query = query & Q(company=company)
    # print(query)
    vehical_names = VehicalName.objects.filter(query)
    # print(vehical_names)
    data = serializers.serialize('json', vehical_names)

    return HttpResponse(data, content_type='application/json')

def ajax_VehicleTypeByGroup(request,group):

	print(group)

	groups= [x.strip() for x in group.split(',')]
	query = Q(group=groups[0])
	for i,g in enumerate(groups):
		if i==0:
			continue

		query= query | Q(group=g)
	print(query)
	vehicle_type=VehicalType.objects.filter(query)
	print(vehicle_type)
	data = serializers.serialize('json', vehicle_type)
	return HttpResponse(data, content_type='application/json')

def ajax_VehicleCompanyByType(request,group,type):
	print(group)
	vehicle_company=VehicalCompany.objects.filter(group=group,type=type)
	print(vehicle_company)
	data = serializers.serialize('json', vehicle_company)
	return HttpResponse(data, content_type='application/json')
