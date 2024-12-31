import time
import threading

class Timer:
    def __init__(self, hours, minutes, seconds):

        self.initial_seconds = hours * 3600 + minutes * 60 + seconds
        self.total_seconds = self.initial_seconds
        self.remaining_seconds = self.initial_seconds
        self.running = False
        self.paused = False

    def start(self):
        """타이머를 시작하거나 다시 시작합니다."""
        if self.running:
            print(f"{self.name} 타이머가 이미 실행 중입니다.")
            return

        self.running = True
        self.paused = False
        threading.Thread(target=self._run).start()

    def stop(self):
        self.running = False

    def pause(self):
        if not self.running:
            return

        self.paused = True
        self.running = False
        print(f"{self.name} 타이머가 일시 정지되었습니다. 남은 시간: {self._format_time(self.remaining_seconds)}")

    def reset(self):
        self.remaining_seconds = self.initial_seconds
        self.running = False
        self.paused = False

    def _run(self):
        while self.running and self.remaining_seconds > 0:
            hours, remainder = divmod(self.remaining_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"{self.name}: {hours}시간 {minutes}분 {seconds}초 남음")
            time.sleep(1)
            self.remaining_seconds -= 1

        if self.remaining_seconds == 0:
            print(f"{self.name} 타이머가 종료되었습니다.")
        self.running = False

    def _format_time(self, total_seconds):
        """총 초를 시:분:초 형식의 문자열로 변환합니다."""
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}시간 {minutes}분 {seconds}초"


