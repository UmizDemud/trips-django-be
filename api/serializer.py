from rest_framework import serializers
from .models import Trip, Logbook, Increment, Remark, Location

import random
from datetime import timedelta


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"

class TripSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True)

    class Meta:
        model = Trip
        fields = "__all__"

    def create(self, validated_data):
        locations_data = validated_data.pop("locations")
        trip = Trip.objects.create(**validated_data)

        for location_data in locations_data:
            location, _ = Location.objects.get_or_create(**location_data)  # Avoid duplicate locations
            trip.locations.add(location)

        # Create Logbook objects (and associated increments) for the trip
        create_roadmap_for_trip(trip)

        return trip


class RemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Remark
        fields = "__all__"


class IncrementSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True, read_only=False)  # Allow id to be written
    remark = RemarkSerializer(required=False, allow_null=True)  # Nested remark

    class Meta:
        model = Increment
        fields = "__all__"

    def validate_duty_status(self, value):
        """Ensure duty_status is one of the valid choices"""
        if value not in dict(Increment.DUTY_STATUS_CHOICES):
            raise serializers.ValidationError(f"Invalid duty_status: {value}")
        return value
      
    def create(self, validated_data):
        remark_data = validated_data.pop('remark', None)  # Get remark data
        if remark_data:
            remark_instance = Remark.objects.create(**remark_data)  # Create the remark instance
            validated_data['remark'] = remark_instance  # Assign the created remark instance

        increment = Increment.objects.create(**validated_data)  # Create the increment instance
        return increment


class LogbookSerializer(serializers.ModelSerializer):
    increments = IncrementSerializer(many=True)  # Nested increments

    class Meta:
        model = Logbook
        fields = "__all__"

    def validate_increments(self, value):
        """Ensure logbook has exactly 48 increments"""
        if not isinstance(value, list) or len(value) != 48:
            raise serializers.ValidationError("Logbook must have exactly 48 increments.")
        return value

    def create(self, validated_data):
        increments_data = validated_data.pop("increments")  # Extract increments data
        logbook = Logbook.objects.create(**validated_data)  # Create logbook first

        # Create increments, linking them to the new logbook
        for increment_data in increments_data:
            # Set the logbook reference for this increment
            increment_data["logbook"] = logbook

            # If 'remark' is present and is a dict, create a Remark instance
            remark_data = increment_data.get("remark")
            if remark_data and isinstance(remark_data, dict):
                remark_instance = Remark.objects.create(**remark_data)
                increment_data["remark"] = remark_instance

            # Create the Increment instance
            Increment.objects.create(**increment_data)

        return logbook

    def update(self, instance, validated_data):
        increments_data = validated_data.pop('increments', None)
        # Save any top-level changes (if any)
        instance.save()

        if increments_data:
            for increment_data in increments_data:
                increment_id = increment_data.get('id')

                try:
                    increment_instance = instance.increments.get(id=increment_id)
                except Increment.DoesNotExist:
                    print("Increment with id", increment_id, "not found.")
                    continue

                # Update dutyStatus if provided
                if 'dutyStatus' in increment_data:
                    increment_instance.dutyStatus = increment_data.get('dutyStatus', increment_instance.dutyStatus)
                
                # Update the remark field if present
                if 'remark' in increment_data:
                    remark_data = increment_data.get('remark')
                    if remark_data:
                        if increment_instance.remark:

                            for field, value in remark_data.items():
                                setattr(increment_instance.remark, field, value)
                            increment_instance.remark.save()
                        else:

                            increment_instance.remark = Remark.objects.create(**remark_data)
                    else:

                        increment_instance.remark = None
                
                increment_instance.save()
        return instance

def create_roadmap_for_trip(trip):
    # 1. Determine total required driving time (in minutes)
    last_location = trip.locations.last()
    total_trip_time_required = (last_location.time if last_location and last_location.time is not None else 0) / 60

    # 2. Build a sorted list of stop locations (for pickups/dropoffs) by their time thresholds
    stop_locations = sorted(
        [loc for loc in trip.locations.all() if loc.type in ['pickup', 'dropoff'] and loc.time is not None],
        key=lambda loc: loc.time
    )
    next_stop_idx = 0

    # 3. Define driving limit: 70 hours (4200 minutes) in any 8-day window
    possible_active_start_offsets = [300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600]  # minutes from midnight
    allowed_driving_minutes = 70 * 60
    driving_minutes_by_day = {}  # Tracks driving minutes per day
    cumulative_driving_minutes = float(trip.cycle_hours * 60)
    current_day = 0
    logbooks = []

    # 4. Loop until we've accumulated the required driving minutes
    while cumulative_driving_minutes < total_trip_time_required:
        day_start = trip.start_date + timedelta(days=current_day)


        active_offset = random.choice(possible_active_start_offsets)
        active_start = day_start + timedelta(minutes=active_offset)
        active_start_index = active_offset // 30  # each increment represents 30 minutes

        # Randomize active end index (active end between indices 36 and 46)
        active_end_index = random.choice(range(32, 44))

        # Create the day's Logbook
        logbook = Logbook.objects.create(trip=trip, date=day_start)
        logbooks.append(logbook)
        driving_minutes_by_day[current_day] = 0

        skip_next = False

        # 5. Create 48 increments for the day
        for inc in range(48):
            # Default: no remark (i.e. remark remains None)
            status = None

            if inc < active_start_index:
                status = "OFF DUTY"
            elif inc >= active_end_index and inc < 47:
                status = "OFF DUTY"
            elif inc == 47:
                status = "SLEEPER BERTH"
            else:
                # Within active period
                if active_start_index <= inc < active_start_index + 2:
                    status = "ON DUTY"
                elif skip_next:
                    status = "ON DUTY"
                    skip_next = False
                else:
                    # Check if it's time for a scheduled stop based on stop locations
                    if (next_stop_idx < len(stop_locations) and 
                        (cumulative_driving_minutes / 60.0) >= stop_locations[next_stop_idx].time):
                        status = "ON DUTY"
                        skip_next = True  # Next increment is part of the same stop block
                        next_stop_idx += 1
                    else:
                        # Decide based on the 8-day rolling driving limit
                        window_start_day = max(0, current_day - 7)
                        driving_in_window = sum(driving_minutes_by_day.get(d, 0) for d in range(window_start_day, current_day + 1))
                        if driving_in_window + 30 <= allowed_driving_minutes:
                            status = "DRIVING"
                            cumulative_driving_minutes += 30
                            driving_minutes_by_day[current_day] += 30
                        else:
                            status = "OFF DUTY"

            # Create the Increment for this 30-minute block; remark remains None
            Increment.objects.create(logbook=logbook, dutyStatus=status, remark=None)

        current_day += 1

    return logbooks

