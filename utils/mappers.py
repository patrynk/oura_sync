"""Mappers to convert JSON data from Oura API to database models."""
import json
from datetime import datetime
from typing import Any

from models.daily_activity import DailyActivity
from models.daily_readiness import DailyReadiness
from models.daily_sleep import DailySleep
from models.daily_spo2 import DailySpo2
from models.daily_stress import DailyStress


def map_daily_sleep(data: dict[str, Any], user_id: str) -> DailySleep:
    """Map JSON data to DailySleep model.

    Args:
        data: JSON data from Oura API
        user_id: User ID to associate with the record

    Returns:
        DailySleep model instance
    """
    contributors = data.get("contributors", {})

    return DailySleep(
        id=data["id"],
        user_id=user_id,
        # Core fields
        day=datetime.strptime(data["day"], "%Y-%m-%d").date(),
        score=data.get("score"),
        timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
        # Contributors - extracted from nested object
        deep_sleep=contributors.get("deep_sleep"),
        efficiency=contributors.get("efficiency"),
        latency=contributors.get("latency"),
        rem_sleep=contributors.get("rem_sleep"),
        restfulness=contributors.get("restfulness"),
        timing=contributors.get("timing"),
        total_sleep=contributors.get("total_sleep"),
        # Store complete JSON
        raw_data=json.dumps(data)
    )


def map_daily_readiness(data: dict[str, Any], user_id: str) -> DailyReadiness:
    """Map JSON data to DailyReadiness model.

    Args:
        data: JSON data from Oura API
        user_id: User ID to associate with the record

    Returns:
        DailyReadiness model instance
    """
    contributors = data.get("contributors", {})

    return DailyReadiness(
        id=data["id"],
        user_id=user_id,
        # Core fields
        day=datetime.strptime(data["day"], "%Y-%m-%d").date(),
        score=data.get("score"),
        timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
        temperature_deviation=data.get("temperature_deviation"),
        temperature_trend_deviation=data.get("temperature_trend_deviation"),
        # Contributors - extracted from nested object
        activity_balance=contributors.get("activity_balance"),
        body_temperature=contributors.get("body_temperature"),
        hrv_balance=contributors.get("hrv_balance"),
        previous_day_activity=contributors.get("previous_day_activity"),
        previous_night=contributors.get("previous_night"),
        recovery_index=contributors.get("recovery_index"),
        resting_heart_rate=contributors.get("resting_heart_rate"),
        sleep_balance=contributors.get("sleep_balance"),
        sleep_regularity=contributors.get("sleep_regularity"),
        # Store complete JSON
        raw_data=json.dumps(data)
    )


def map_daily_spo2(data: dict[str, Any], user_id: str) -> DailySpo2:
    """Map JSON data to DailySpo2 model.

    Args:
        data: JSON data from Oura API
        user_id: User ID to associate with the record

    Returns:
        DailySpo2 model instance
    """
    spo2_percentage = data.get("spo2_percentage", {})

    return DailySpo2(
        id=data["id"],
        user_id=user_id,
        # Core fields
        day=datetime.strptime(data["day"], "%Y-%m-%d").date(),
        breathing_disturbance_index=data.get("breathing_disturbance_index"),
        spo2_percentage_average=spo2_percentage.get("average"),
        # Store complete JSON
        raw_data=json.dumps(data)
    )


def map_daily_stress(data: dict[str, Any], user_id: str) -> DailyStress:
    """Map JSON data to DailyStress model.

    Args:
        data: JSON data from Oura API
        user_id: User ID to associate with the record

    Returns:
        DailyStress model instance
    """
    return DailyStress(
        id=data["id"],
        user_id=user_id,
        # Core fields
        day=datetime.strptime(data["day"], "%Y-%m-%d").date(),
        day_summary=data.get("day_summary"),
        recovery_high=data.get("recovery_high"),
        stress_high=data.get("stress_high"),
        # Store complete JSON
        raw_data=json.dumps(data)
    )


def map_daily_activity(data: dict[str, Any], user_id: str) -> DailyActivity:
    """Map JSON data to DailyActivity model.

    Args:
        data: JSON data from Oura API
        user_id: User ID to associate with the record

    Returns:
        DailyActivity model instance
    """
    contributors = data.get("contributors", {})
    met = data.get("met", {})

    return DailyActivity(
        id=data["id"],
        user_id=user_id,
        # Core fields
        day=datetime.strptime(data["day"], "%Y-%m-%d").date(),
        score=data.get("score"),
        timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
        # Activity metrics
        active_calories=data.get("active_calories"),
        average_met_minutes=data.get("average_met_minutes"),
        equivalent_walking_distance=data.get("equivalent_walking_distance"),
        high_activity_met_minutes=data.get("high_activity_met_minutes"),
        high_activity_time=data.get("high_activity_time"),
        inactivity_alerts=data.get("inactivity_alerts"),
        low_activity_met_minutes=data.get("low_activity_met_minutes"),
        low_activity_time=data.get("low_activity_time"),
        medium_activity_met_minutes=data.get("medium_activity_met_minutes"),
        medium_activity_time=data.get("medium_activity_time"),
        meters_to_target=data.get("meters_to_target"),
        non_wear_time=data.get("non_wear_time"),
        resting_time=data.get("resting_time"),
        sedentary_met_minutes=data.get("sedentary_met_minutes"),
        sedentary_time=data.get("sedentary_time"),
        steps=data.get("steps"),
        target_calories=data.get("target_calories"),
        target_meters=data.get("target_meters"),
        total_calories=data.get("total_calories"),
        # Activity classification
        class_5_min=data.get("class_5_min"),
        # MET interval - extracted from nested object
        met_interval=met.get("interval"),
        # Contributors - extracted from nested object
        meet_daily_targets=contributors.get("meet_daily_targets"),
        move_every_hour=contributors.get("move_every_hour"),
        recovery_time=contributors.get("recovery_time"),
        stay_active=contributors.get("stay_active"),
        training_frequency=contributors.get("training_frequency"),
        training_volume=contributors.get("training_volume"),
        # Store complete JSON (includes met.items array and timestamp)
        raw_data=json.dumps(data)
    )


# Mapper registry for easy lookup
MAPPERS = {
    "daily_activity": map_daily_activity,
    "daily_sleep": map_daily_sleep,
    "daily_readiness": map_daily_readiness,
    "daily_spo2": map_daily_spo2,
    "daily_stress": map_daily_stress,
}
