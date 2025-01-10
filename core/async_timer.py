# your_project/core/async_timer.py

import asyncio

class AsyncTimer:
    def __init__(self, hours, minutes, seconds, on_tick_callback=None, on_timeout_callback=None):
        # 초기 시간 설정
        self.initial_seconds = hours * 3600 + minutes * 60 + seconds
        self.remaining_seconds = self.initial_seconds

        # 상태 플래그
        self.running = False
        self.paused = False

        # 콜백
        self.on_tick_callback = on_tick_callback
        self.on_timeout_callback = on_timeout_callback

        # 내부용
        self._task = None              # asyncio.Task (타이머 실행)
        self._pause_event = asyncio.Event()
        self._pause_event.set()        # 초기에 pause 상태가 아님

    def set_time(self, hours, minutes, seconds):
        """타이머의 초기/남은 시간을 재설정"""
        self.initial_seconds = hours * 3600 + minutes * 60 + seconds
        self.remaining_seconds = self.initial_seconds

    async def start(self):
        """비동기로 타이머 시작"""
        print("[group.py] reset() ",self.running)
        if self.running:
            print("[AsyncTimer] 이미 실행 중입니다.")
            return

        self.running = True
        self.paused = False
        self._pause_event.set()  # pause 해제

        # 타이머 코루틴을 Task로 실행
        print("[async_timer] self.running",self.running)
        self._task = asyncio.create_task(self._run_timer())
        print("[AsyncTimer] 타이머 시작")

    async def stop(self):
        """타이머 완전 중지"""
        if not self.running:
            return

        self.running = False
        self.paused = False
        self._pause_event.set()  # 혹시 일시정지 중이라면 해제

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("[AsyncTimer] 타이머 중지")

    async def pause(self):
        # """타이머 일시 정지"""
        # if not self.running or self.paused:
        #     return
        # self.paused = True
        self._pause_event.clear()  # 대기 상태
        print(f"[AsyncTimer] 일시 정지, 남은 시간: {self.remaining_seconds}초")

    async def resume(self):
        # print("in resume", self._pause_event)
        # """일시 정지된 타이머 재개"""
        # if not self.paused:
        #     return
        # self.paused = False
        self._pause_event.set()
        print("in resume", self._pause_event)
        print(f"[AsyncTimer] 재개, 남은 시간: {self.remaining_seconds}초")

    async def reset(self):
        """타이머 초기화 (초기값으로 복원)"""
        await self.stop()
        self.remaining_seconds = self.initial_seconds
        print(f"[AsyncTimer] 리셋 완료 {self.remaining_seconds}")

    async def _run_timer(self):
        """비동기 타이머 동작 코루틴"""
        print("in _run_timer",self.running, self.remaining_seconds)
        try:
            while self.running and not self.paused and self.remaining_seconds > 0:
                # 일시정지 상태라면, 이벤트가 set될 때까지 대기
                await self._pause_event.wait()

                # 1초마다 남은 시간 감소
                # Tick 콜백
                if self.on_tick_callback:
                    await self._invoke_callback(self.on_tick_callback, self.remaining_seconds)
                await asyncio.sleep(1)
                self.remaining_seconds -= 1

            # 타이머가 0초에 도달
            if self.running and self.remaining_seconds <= 0:
                print("[AsyncTimer] 타이머가 종료되었습니다.")
                if self.on_timeout_callback:
                    await self._invoke_callback(self.on_timeout_callback)
        except asyncio.CancelledError:
            # stop() 호출 시 Task가 취소
            pass
        # finally:
        #     print("finally")
        #     # 종료 시 상태 초기화
        #     self.running = False

    async def _invoke_callback(self, callback, *args):
        """동기/비동기 콜백 둘 다 지원"""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args)
        else:
            callback(*args)
