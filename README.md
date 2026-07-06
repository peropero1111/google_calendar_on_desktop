# google_calendar_on_desktop
[exe 파일링크](https://drive.google.com/drive/folders/1IbY2NH5m0-zS1GZNa5uw_mFJOuiKGH03?usp=sharing)로 실행할때의 사용법은 글 하단에 있습니다.
</br>
</br>
사용하시기전에 다음 절차를 따라 주십시오.
</br>
아래에 더욱 쉬운 이해를 위한 이미지가 있습니다. 

## 1. 설치
&nbsp;&nbsp;&nbsp;&nbsp;1.1 적당한 폴더에 google_calendar_on_desktop 속 내용물을 다운 받아 주십시오.


&nbsp;&nbsp;&nbsp;&nbsp;1.2 google_calendar_on_desktop 속 calendar.py 에서 다음 명령어를 각각 입력하여 주십시오.
```powershell
python -m pip install requests
python -m pip install icalendar
python -m pip install recurring-ical-events
python -m pip install tzdata
```
</br>

## 2. Google Calendar 연결

&nbsp;&nbsp;&nbsp;&nbsp;2.1. 브라우저에서 Google Calendar를 엽니다.  
&nbsp;&nbsp;&nbsp;&nbsp;2.2. 오른쪽 위 톱니바퀴 아이콘에서 `설정`으로 들어갑니다.  
&nbsp;&nbsp;&nbsp;&nbsp;2.3. 왼쪽에서 `내 캘린더의 설정`을 선택한 후 선택할 계정을 고릅니다.  
&nbsp;&nbsp;&nbsp;&nbsp;2.4. `캘린더 통합` 을 선택한 후 암호화 형식인 `iCal 형식의 비공개 주소`를 복사합니다.  
&nbsp;&nbsp;&nbsp;&nbsp;2.5. calendar.py를 처음 실행하면 생기는 `calendar_widget_config.json` 파일을 열고 `input_ical_urls`에 붙여 넣습니다.

</br>

## 3. 작업스케쥴러 등록 (선택사항) (py 버젼) 
&nbsp;&nbsp;&nbsp;&nbsp;3.1 작업스케줄러를 실행시킨후 작업만들기를 클릭하여 주십시오.

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20212029.png" width="450" height="450"/>  
</br>

&nbsp;&nbsp;&nbsp;&nbsp;3.2 처음뜨는 창 (일반 메뉴) 에서 이름을 정해 주시고 `사용자가 로그온 할때만 실행` 으로 설정해 주십시오.

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30 212122.png" width="450" height="450"/> 
</br>
</br>

&nbsp;&nbsp;&nbsp;&nbsp;3.3 트리거 메뉴로 넘어가서 새로만들기를 눌러주십시오.

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20212201.png" width="450" height="450"/> 
</br>
</br>

&nbsp;&nbsp;&nbsp;&nbsp;3.4 작업시작을 `로그온 할떄`, 지연시간에 체크해 주시고 30초 로 체크해 주십시오

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20212231.png" width="450" height="450"/> 
</br>
</br>

&nbsp;&nbsp;&nbsp;&nbsp;3.5 cmd 혹은 powershell 을 관리자 권한으로 실행시켜서 ```  where pythonw  ``` 라고 검색 해 주십시오.
</br>&nbsp;&nbsp;&nbsp;&nbsp;( 저는 python 을 기존에 다운 하여서 두번째 경로가 있는데 대부분의 사람들은 첫번째 경로 밖에 없을 것입니다. 무엇으로 하여도 결과에 큰 지장은 없습니다. )

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20215110.png" width="450" height="450"/> 
<br>
</br>

&nbsp;&nbsp;&nbsp;&nbsp;3.6 나온 경로를 기억하고 있다가 동작 메뉴로 넘어가서 새로만들기를 눌러 주십시오.

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20212311.png" width="450" height="450"/> 
<br>
</br>

&nbsp;&nbsp;&nbsp;&nbsp;3.7 `프로그램`에 나온 경로를 입력하여 주십시오. 
</br>&nbsp;&nbsp;&nbsp;&nbsp;3.8 `인수 추가` 에 다음과 같이 입력하여 주십시오 `"C:\Users\~ run_widget.py 를 놓은 폴더 경로 주소 ~ \run_widget.py"`
</br>&nbsp;&nbsp;&nbsp;&nbsp;3.9 `시작 위치` 에 다음과 같이 입력하여 주십시오  `C:\Users\~ run_widget.py 를 놓은 폴더 경로 주소 ~`

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20212838.png" width="450" height="450"/> 
<br>
</br>

## 4. 작업스케쥴러 등록 (선택사항) (exe 버젼) 

&nbsp;&nbsp;&nbsp;&nbsp;4.1 작업스케줄러를 실행시킨후 작업만들기를 클릭하여 주십시오.

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20212029.png" width="450" height="450"/>  
</br>

&nbsp;&nbsp;&nbsp;&nbsp;4.2 처음뜨는 창 (일반 메뉴) 에서 이름을 정해 주시고 `사용자가 로그온 할때만 실행` 으로 설정해 주십시오.

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30 212122.png" width="450" height="450"/> 
</br>
</br>

&nbsp;&nbsp;&nbsp;&nbsp;4.3 트리거 메뉴로 넘어가서 새로만들기를 눌러주십시오.

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30 212201.png" width="450" height="450"/> 
</br>
</br>

&nbsp;&nbsp;&nbsp;&nbsp;4.4 작업시작을 `로그온 할떄`, 지연시간에 체크해 주시고 30초 로 체크해 주십시오

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20212231.png" width="450" height="450"/> 
</br>
</br>

&nbsp;&nbsp;&nbsp;&nbsp;4.6 동작 메뉴로 넘어가서 새로만들기를 눌러 주십시오.

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20212311.png" width="450" height="450"/> 
<br>
</br>


&nbsp;&nbsp;&nbsp;&nbsp;4.7 `프로그램`에 exe 파일의 경로를 입력하여 주십시오. 
</br>&nbsp;&nbsp;&nbsp;&nbsp;4.8 `인수 추가` 에 다음과 같이 입력하여 주십시오 `"C:\Users\~ google_calendar_on_desktop.exe 를 놓은 폴더 경로 주소 ~ \google_calendar_on_desktop.exe"`
</br>&nbsp;&nbsp;&nbsp;&nbsp;4.9 `시작 위치` 에 다음과 같이 입력하여 주십시오  `C:\Users\~ google_calendar_on_desktop.exe 를 놓은 폴더 경로 주소 ~`

&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-06-30%20224842.png" width="450" height="450"/> 
<br>
</br>

## 5. 기타 사용법 

&nbsp;&nbsp;&nbsp;&nbsp;프로그램 실행후 `오른쪽 위의` 선택 버튼을 누른 후
</br>
</br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-07-03%20181439.png" width="450" height="450"/> 

&nbsp;&nbsp;&nbsp;&nbsp;숨기고 싶은 일정을 선택한 다음
</br>
</br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-07-03%20181547.png" width="450" height="450"/> 

&nbsp;&nbsp;&nbsp;&nbsp;`완료` 버튼을 누르면 선택하였던 일정이 유저가 `해제처리 하기전까지` 숨김처리 됩니다.
</br>
</br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-07-03%20181643.png" width="450" height="450"/> 
</br>
</br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/google_calendar_on_desktop/blob/main/img/2026-07-03%20181610.png" width="450" height="450"/> 
</br>
</br>
&nbsp;&nbsp;&nbsp;&nbsp;해제처리하는 방법은 일정을 `숨김처리 하는 방법과 같으므로` 설명은 생략하겠습니다.


