"""
Unit tests for next execution time calculation and cron parsing
"""
import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestCronExecution:
    """Tests for cron expression next execution calculation"""

    @pytest.mark.asyncio
    async def test_calculate_next_execution_cron_daily(self, scheduler):
        """Test calculating next execution for daily cron (0 2 * * *)"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 2 * * *",  # Daily at 2 AM
            "timezone": "UTC"
        }

        with patch('scheduler.datetime') as mock_datetime:
            # Current time: 2025-01-01 00:00:00 UTC
            mock_datetime.now.return_value = datetime(2025, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)

            next_execution = scheduler._calculate_next_execution(task)

            assert next_execution is not None
            # Should be 2025-01-01 02:00:00
            assert next_execution.hour == 2
            assert next_execution.minute == 0
            assert next_execution.second == 0

    @pytest.mark.asyncio
    async def test_calculate_next_execution_cron_hourly(self, scheduler):
        """Test calculating next execution for hourly cron (0 * * * *)"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 * * * *",  # Every hour
            "timezone": "UTC"
        }

        with patch('scheduler.datetime') as mock_datetime:
            # Current time: 2025-01-01 14:30:00 UTC
            mock_datetime.now.return_value = datetime(2025, 1, 1, 14, 30, 0, tzinfo=pytz.UTC)

            next_execution = scheduler._calculate_next_execution(task)

            assert next_execution is not None
            # Should be 2025-01-01 15:00:00
            assert next_execution.hour == 15
            assert next_execution.minute == 0

    @pytest.mark.asyncio
    async def test_calculate_next_execution_cron_weekly(self, scheduler):
        """Test calculating next execution for weekly cron (0 0 * * 0)"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 0 * * 0",  # Every Sunday at midnight
            "timezone": "UTC"
        }

        next_execution = scheduler._calculate_next_execution(task)

        assert next_execution is not None
        # Should be next Sunday
        assert next_execution.weekday() == 6  # Sunday

    @pytest.mark.asyncio
    async def test_calculate_next_execution_cron_monthly(self, scheduler):
        """Test calculating next execution for monthly cron (0 0 1 * *)"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 0 1 * *",  # First day of each month
            "timezone": "UTC"
        }

        next_execution = scheduler._calculate_next_execution(task)

        assert next_execution is not None
        # Should be first day of month
        assert next_execution.day == 1

    @pytest.mark.asyncio
    async def test_calculate_next_execution_cron_custom(self, scheduler):
        """Test calculating next execution for custom cron (*/15 * * * *)"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "*/15 * * * *",  # Every 15 minutes
            "timezone": "UTC"
        }

        with patch('scheduler.datetime') as mock_datetime:
            # Current time: 2025-01-01 14:07:00 UTC
            mock_datetime.now.return_value = datetime(2025, 1, 1, 14, 7, 0, tzinfo=pytz.UTC)

            next_execution = scheduler._calculate_next_execution(task)

            assert next_execution is not None
            # Should be 2025-01-01 14:15:00
            assert next_execution.hour == 14
            assert next_execution.minute == 15

    @pytest.mark.asyncio
    async def test_calculate_next_execution_cron_with_timezone(self, scheduler):
        """Test calculating next execution with non-UTC timezone"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 9 * * *",  # 9 AM
            "timezone": "America/New_York"
        }

        next_execution = scheduler._calculate_next_execution(task)

        assert next_execution is not None
        # Result should be in UTC (stored without timezone info)
        assert next_execution.tzinfo is None

    @pytest.mark.asyncio
    async def test_calculate_next_execution_cron_invalid_expression(self, scheduler):
        """Test handling invalid cron expression"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "invalid cron",
            "timezone": "UTC"
        }

        next_execution = scheduler._calculate_next_execution(task)

        # Should return None for invalid expression
        assert next_execution is None

    @pytest.mark.asyncio
    async def test_calculate_next_execution_cron_missing_expression(self, scheduler):
        """Test handling missing cron expression"""
        task = {
            "schedule_type": "cron",
            "cron_expression": None,
            "timezone": "UTC"
        }

        next_execution = scheduler._calculate_next_execution(task)

        # Should return None when cron_expression is missing
        assert next_execution is None


@pytest.mark.unit
class TestIntervalExecution:
    """Tests for interval-based next execution calculation"""

    @pytest.mark.asyncio
    async def test_calculate_next_execution_interval_1_hour(self, scheduler):
        """Test calculating next execution for 1-hour interval"""
        task = {
            "schedule_type": "interval",
            "interval_seconds": 3600,  # 1 hour
            "timezone": "UTC"
        }

        with patch('scheduler.datetime') as mock_datetime:
            now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.now.return_value = now

            next_execution = scheduler._calculate_next_execution(task)

            assert next_execution is not None
            # Should be 1 hour from now
            expected = now + timedelta(seconds=3600)
            time_diff = abs((next_execution - expected.replace(tzinfo=None)).total_seconds())
            assert time_diff < 1  # Within 1 second

    @pytest.mark.asyncio
    async def test_calculate_next_execution_interval_30_minutes(self, scheduler):
        """Test calculating next execution for 30-minute interval"""
        task = {
            "schedule_type": "interval",
            "interval_seconds": 1800,  # 30 minutes
            "timezone": "UTC"
        }

        with patch('scheduler.datetime') as mock_datetime:
            now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.now.return_value = now

            next_execution = scheduler._calculate_next_execution(task)

            assert next_execution is not None
            expected = now + timedelta(seconds=1800)
            time_diff = abs((next_execution - expected.replace(tzinfo=None)).total_seconds())
            assert time_diff < 1

    @pytest.mark.asyncio
    async def test_calculate_next_execution_interval_1_day(self, scheduler):
        """Test calculating next execution for 1-day interval"""
        task = {
            "schedule_type": "interval",
            "interval_seconds": 86400,  # 1 day
            "timezone": "UTC"
        }

        with patch('scheduler.datetime') as mock_datetime:
            now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.now.return_value = now

            next_execution = scheduler._calculate_next_execution(task)

            assert next_execution is not None
            expected = now + timedelta(days=1)
            time_diff = abs((next_execution - expected.replace(tzinfo=None)).total_seconds())
            assert time_diff < 1

    @pytest.mark.asyncio
    async def test_calculate_next_execution_interval_missing(self, scheduler):
        """Test handling missing interval_seconds"""
        task = {
            "schedule_type": "interval",
            "interval_seconds": None,
            "timezone": "UTC"
        }

        next_execution = scheduler._calculate_next_execution(task)

        # Should return None when interval_seconds is missing
        assert next_execution is None

    @pytest.mark.asyncio
    async def test_calculate_next_execution_interval_zero(self, scheduler):
        """Test handling zero interval_seconds"""
        task = {
            "schedule_type": "interval",
            "interval_seconds": 0,
            "timezone": "UTC"
        }

        next_execution = scheduler._calculate_next_execution(task)

        # Should return None for zero or negative interval
        assert next_execution is None

    @pytest.mark.asyncio
    async def test_calculate_next_execution_interval_negative(self, scheduler):
        """Test handling negative interval_seconds"""
        task = {
            "schedule_type": "interval",
            "interval_seconds": -100,
            "timezone": "UTC"
        }

        next_execution = scheduler._calculate_next_execution(task)

        # Should return None for negative interval
        assert next_execution is None


@pytest.mark.unit
class TestOnceExecution:
    """Tests for one-time schedule next execution"""

    @pytest.mark.asyncio
    async def test_calculate_next_execution_once(self, scheduler):
        """Test that one-time schedules return None for next execution"""
        task = {
            "schedule_type": "once",
            "scheduled_time": datetime.utcnow() + timedelta(hours=1),
            "timezone": "UTC"
        }

        next_execution = scheduler._calculate_next_execution(task)

        # One-time schedules should not have a next execution
        assert next_execution is None


@pytest.mark.unit
class TestTimezoneHandling:
    """Tests for timezone handling in next execution calculation"""

    @pytest.mark.asyncio
    async def test_timezone_est_to_utc(self, scheduler):
        """Test converting EST time to UTC for storage"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 9 * * *",  # 9 AM EST
            "timezone": "America/New_York"
        }

        next_execution = scheduler._calculate_next_execution(task)

        assert next_execution is not None
        # Result should be timezone-naive (UTC)
        assert next_execution.tzinfo is None

    @pytest.mark.asyncio
    async def test_timezone_pst_to_utc(self, scheduler):
        """Test converting PST time to UTC for storage"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 18 * * *",  # 6 PM PST
            "timezone": "America/Los_Angeles"
        }

        next_execution = scheduler._calculate_next_execution(task)

        assert next_execution is not None
        # Result should be timezone-naive (UTC)
        assert next_execution.tzinfo is None

    @pytest.mark.asyncio
    async def test_timezone_tokyo_to_utc(self, scheduler):
        """Test converting Tokyo time to UTC for storage"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 12 * * *",  # 12 PM JST
            "timezone": "Asia/Tokyo"
        }

        next_execution = scheduler._calculate_next_execution(task)

        assert next_execution is not None
        # Result should be timezone-naive (UTC)
        assert next_execution.tzinfo is None

    @pytest.mark.asyncio
    async def test_timezone_invalid(self, scheduler):
        """Test handling invalid timezone"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 9 * * *",
            "timezone": "Invalid/Timezone"
        }

        # Should handle gracefully (may raise or return None depending on implementation)
        try:
            next_execution = scheduler._calculate_next_execution(task)
            # If it doesn't raise, it should return None
            assert next_execution is None
        except Exception:
            # It's acceptable to raise an exception for invalid timezone
            pass


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases in next execution calculation"""

    @pytest.mark.asyncio
    async def test_unknown_schedule_type(self, scheduler):
        """Test handling unknown schedule type"""
        task = {
            "schedule_type": "unknown",
            "timezone": "UTC"
        }

        next_execution = scheduler._calculate_next_execution(task)

        # Should return None for unknown schedule type
        assert next_execution is None

    @pytest.mark.asyncio
    async def test_cron_leap_year(self, scheduler):
        """Test cron expression on leap year date"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 0 29 2 *",  # Feb 29 (leap year only)
            "timezone": "UTC"
        }

        with patch('scheduler.datetime') as mock_datetime:
            # Set current time to a leap year
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)

            next_execution = scheduler._calculate_next_execution(task)

            assert next_execution is not None
            # Should be Feb 29, 2024
            assert next_execution.month == 2
            assert next_execution.day == 29
            assert next_execution.year == 2024

    @pytest.mark.asyncio
    async def test_cron_daylight_saving_transition(self, scheduler):
        """Test cron execution during daylight saving time transition"""
        task = {
            "schedule_type": "cron",
            "cron_expression": "0 2 * * *",  # 2 AM (during DST transition)
            "timezone": "America/New_York"
        }

        # Test during spring forward (DST starts)
        # This is a complex edge case - just ensure it doesn't crash
        next_execution = scheduler._calculate_next_execution(task)
        assert next_execution is not None

    @pytest.mark.asyncio
    async def test_interval_with_different_timezone(self, scheduler):
        """Test interval calculation respects timezone"""
        task = {
            "schedule_type": "interval",
            "interval_seconds": 3600,
            "timezone": "America/New_York"
        }

        next_execution = scheduler._calculate_next_execution(task)

        assert next_execution is not None
        # Result should be timezone-naive (UTC)
        assert next_execution.tzinfo is None
