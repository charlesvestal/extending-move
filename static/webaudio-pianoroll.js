customElements.define("webaudio-pianoroll", class Pianoroll extends HTMLElement {
    constructor(){
        super();
    }
    defineprop(){
        const plist=this.module.properties;
        for(let k in plist){
            const v = plist[k];
            this["_"+k] = this.getAttr(k,v.value);
            Object.defineProperty(this, k, {
                get:()=>{return this["_"+k]},
                set:(val)=>{
                    this["_"+k] = val;
                    if(typeof(this[v.observer])=="function")
                        this[v.observer]();
                }
            });
        }        
    }
    connectedCallback(){
        let root;
//        if(this.attachShadow)
//          root=this.attachShadow({mode: 'open'});
//        else
          root=this;
        this.module = {
            is:"webaudio-pianoroll",
            properties:{
                width:              {type:Number, value:640, observer:'layout'},
                height:             {type:Number, value:320, observer:'layout'},
                timebase:           {type:Number, value:16, observer:'layout'},
                editmode:           {type:String, value:"dragpoly"},
                xrange:             {type:Number, value:16, observer:'layout'},
                yrange:             {type:Number, value:16, observer:'layout'},
                xoffset:            {type:Number, value:0, observer:'layout'},
                yoffset:            {type:Number, value:60, observer:'layout'},
                grid:               {type:Number, value:4},
                snap:               {type:Number, value:1},
                wheelzoom:          {type:Number, value:0},
                wheelzoomx:         {type:Number, value:0},
                wheelzoomy:         {type:Number, value:0},
                xscroll:            {type:Number, value:0},
                yscroll:            {type:Number, value:0},
                gridnoteratio:      {type:Number, value:0.5, observer:'updateTimer'},
                xruler:             {type:Number, value:24, observer:'layout'},
                yruler:             {type:Number, value:24, observer:'layout'},
                octadj:             {type:Number, value:-1},
                cursor:             {type:Number, value:0, observer:'redrawMarker'},
                markstart:          {type:Number, value:0, observer:'redrawMarker'},
                markend:            {type:Number, value:16, observer:'redrawMarker'},
                defvelo:            {type:Number, value:100},
                collt:              {type:String, value:"#ccc"},
                coldk:              {type:String, value:"#aaa"},
                colgrid:            {type:String, value:"#666"},
                colnote:            {type:String, value:"#f22"},
                colnotesel:         {type:String, value:"#0f0"},
                colnoteborder:      {type:String, value:"#000"},
                colnoteselborder:   {type:String, value:"#fff"},
                colrulerbg:         {type:String, value:"#666"},
                colrulerfg:         {type:String, value:"#fff"},
                colrulerborder:     {type:String, value:"#000"},
                colselarea:         {type:String, value:"rgba(0,0,0,0.3)"},
                bgsrc:              {type:String, value:null, observer:'layout'},
                cursorsrc:          {type:String, value:"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJub25lIj4NCjxwYXRoIGZpbGw9InJnYmEoMjU1LDEwMCwxMDAsMC44KSIgZD0iTTAsMSAyNCwxMiAwLDIzIHoiLz4NCjwvc3ZnPg0K"},
                cursoroffset:       {type:Number, value:0},
                markstartsrc:       {type:String, value:"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij4NCjxwYXRoIGZpbGw9IiMwYzAiIGQ9Ik0wLDEgMjQsMSAwLDIzIHoiLz4NCjwvc3ZnPg0K"},
                markstartoffset:    {type:Number, value:0},
                markendsrc:         {type:String, value:"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij4NCjxwYXRoIGZpbGw9IiMwYzAiIGQ9Ik0wLDEgMjQsMSAyNCwyMyB6Ii8+DQo8L3N2Zz4NCg=="},
                markendoffset:      {type:Number, value:-24},
                kbsrc:              {type:String, value:"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSI0ODAiIHByZXNlcnZlQXNwZWN0UmF0aW89Im5vbmUiPgo8cGF0aCBmaWxsPSIjZmZmIiBzdHJva2U9IiMwMDAiIGQ9Ik0wLDAgaDI0djQ4MGgtMjR6Ii8+CjxwYXRoIGZpbGw9IiMwMDAiIGQ9Ik0wLDQwIGgxMnY0MGgtMTJ6IE0wLDEyMCBoMTJ2NDBoLTEyeiBNMCwyMDAgaDEydjQwaC0xMnogTTAsMzIwIGgxMnY0MGgtMTJ6IE0wLDQwMCBoMTJ2NDBoLTEyeiIvPgo8cGF0aCBmaWxsPSJub25lIiBzdHJva2U9IiMwMDAiIGQ9Ik0wLDYwIGgyNCBNMCwxNDAgaDI0IE0wLDIyMCBoMjQgTTAsMjgwIGgyNCBNMCwzNDAgaDI0IE0wLDQyMCBoMjQiLz4KPC9zdmc+Cg==", observer:'layout'},
                kbwidth:            {type:Number,value:40},
                loop:               {type:Number, value:0},
                preload:            {type:Number, value:1.0},
                tempo:              {type:Number, value:120, observer:'updateTimer'},
                enable:             {type:Boolean, value:true},
            },
        };
        this.defineprop();
        root.innerHTML =
`<style>
.pianoroll{
    background:#ccc;
}
:host {
    user-select: none;
    display: inline-block;
    font-family: sans-serif;
    font-size: 11px;
    padding:0;
    margin:0;
}
#wac-body {
    position: relative;
    margin:0;
    padding:0;
    width: 100%;
    height: 100%;
    overflow: hidden;
}
#wac-pianoroll {
    cursor: pointer;
    margin:0;
    padding:0;
    width: 100%;
    height: 100%;
    background-size:100% calc(100%*12/16);
    background-position:left bottom;
}
#wac-menu {
    display:none;
    position:absolute;
    top:0px;
    left:0px;
    background:#eef;
    color:#000;
    padding:2px 10px;
    border:1px solid #66f;
    border-radius: 4px;
    cursor:pointer;
}
.marker{
    position: absolute;
    left:0px;
    top:0px;
    cursor:ew-resize;
}
#wac-kb{
    position:absolute;
    left:0px;
    top:0px;
    width:100px;
    height:100%;
    background: repeat-y;
    background-size:100% calc(100%*12/16);
    background-position:left bottom;
}
</style>
<div class="wac-body" id="wac-body" touch-action="none">
<canvas id="wac-pianoroll" touch-action="none" tabindex="0"></canvas>
<div id="wac-kb"></div>
<img id="wac-markstart" class="marker" src="${this.markstartsrc}"/>
<img id="wac-markend" class="marker" src="${this.markendsrc}"/>
<img id="wac-cursor" class="marker" src="${this.cursorsrc}"/>
<div id="wac-menu">Delete</div>
</div>`;

        this.sortSequence=function(){
            this.sequence.sort((x,y)=>{return x.t-y.t;});
        };
        this.findNextEv=function(tick){
            for(let i=0;i<this.sequence.length;++i){
                const nev=this.sequence[i];
                if(nev.t>=this.markend)
                    return {t1:tick,n2:this.markend,dt:this.markend-tick,i:-1};
                if(nev.t>=tick)
                    return {t1:tick,t2:nev.t,dt:nev.t-tick,i:i};
            }
            return {t1:tick,t2:this.markend,dt:this.markend-tick,i:-1};
        };
        this.locate=function(tick){
            this.cursor=tick;
        };
        this.updateTimer=function(){
            this.tick2time=4*60/this.tempo/this.timebase;
        };
        this.play=function(actx,playcallback,tick){
            function Interval(){
                const current=this.actx.currentTime;
                while(this.timestack.length>1 && current>=this.timestack[1][0]){
                    this.timestack.shift();
                }
                this.cursor=this.timestack[0][1]+(current-this.timestack[0][0])/this.timestack[0][2];
                this.redrawMarker();
                while(current+this.preload>=this.time1){
                    this.time0=this.time1;
                    this.tick0=this.tick1;
                    let e=this.sequence[this.index1];
                    if(!e || e.t>=this.markend){
                        this.timestack.push([this.time1,this.markstart,this.tick2time]);
                        const p=this.findNextEv(this.markstart);
                        this.time1+=p.dt*this.tick2time;
                        this.index1=p.i;
                    }
                    else{
                        this.tick1=e.t;
                        this.timestack.push([this.time1,e.t,this.tick2time]);
                        let gmax=Math.min(e.t+e.g,this.markend)-e.t;
                        if(this.editmode=="gridmono"||this.editmode=="gridpoly")
                            gmax*=this.gridnoteratio;
                        const cbev={t:this.time1,g:this.time1+gmax*this.tick2time,n:e.n};
                        if(this.playcallback)
                            this.playcallback(cbev);
                        e=this.sequence[++this.index1];
                        if(!e || e.t>=this.markend){
                            this.time1+=(this.markend-this.tick1)*this.tick2time;
                            const p=this.findNextEv(this.markstart);
                            this.timestack.push([this.time1,this.markstart,this.tick2time]);
                            this.time1+=p.dt*this.tick2time;
                            this.index1=p.i;
                        }
                        else
                            this.time1+=(e.t-this.tick1)*this.tick2time;
                    }
                }
            }
            if(typeof(tick)!="undefined")
                this.locate(tick);
            if(this.timer!=null)
                return;
            this.actx=actx;
            this.playcallback=playcallback;
            this.timestack=[];
            this.time0=this.time1=this.actx.currentTime+0.1;
            this.tick0=this.tick1=this.cursor;
            this.tick2time=4*60/this.tempo/this.timebase;
            const p=this.findNextEv(this.cursor);
            this.index1=p.i;
            this.timestack.push([0,this.cursor,0]);
            this.timestack.push([this.time0,this.cursor,this.tick2time]);
            this.time1+=p.dt*this.tick2time;
            if(p.i<0)
                this.timestack.push([this.time1,this.markstart,this.tick2time]);
            else
                this.timestack.push([this.time1,p.t1,this.tick2time]);
            this.timer=setInterval(Interval.bind(this),25);
        };
        this.stop=function(){
            if(this.timer)
                clearInterval(this.timer);
            this.timer=null;
        };
        this.setMMLString=function(s){
            this.sequence=[];
            let i,l,n,t,defo,defl,tie,evlast;
            const parse={s:s,i:i,tb:this.timebase};
            function getNum(p){
                var n=0;
                while(p.s[p.i]>="0"&&p.s[p.i]<="9"){
                    n=n*10+parseInt(p.s[p.i]);
                    ++p.i;
                }
                return n;
            }
            function getLen(p){
                var n=getNum(p);
                if(n==0)
                    n=defl;
                n=p.tb/n;
                var n2=n;
                while(p.s[p.i]=="."){
                    ++p.i;
                    n+=(n2>>=1);
                }
                return n;
            }
            function getNote(p){
                switch(p.s[p.i]){
                case "c": case "C": n=0; break;
                case "d": case "D": n=2; break;
                case "e": case "E": n=4; break;
                case "f": case "F": n=5; break;
                case "g": case "G": n=7; break;
                case "a": case "A": n=9; break;
                case "b": case "B": n=11; break;
                default:
                    n=-1;
                }
                ++p.i;
                if(n<0)
                    return -1;
                for(;;){
                    switch(p.s[p.i]){
                    case "-": --n; break;
                    case "+": ++n; break;
                    case "#": ++n; break;
                    default:
                        return n;
                    }
                    ++p.i;
                }
            }
            defo=4;
            defl=8;
            t=0;
            tie=0;
            evlast=null;
            for(parse.i=0;parse.i<parse.s.length;){
                switch(parse.s[parse.i]){
                case '>':
                    ++parse.i; ++defo; n=-1; l=0;
                    break;
                case '<':
                    ++parse.i; --defo; n=-1; l=0;
                    break;
                case '&': case '^':
                    ++parse.i; tie=1; n=-1; l=0;
                    break;
                case 't': case 'T':
                    ++parse.i; n=-1; l=0;
                    this.tempo=getNum(parse);
                    break;
                case 'o': case 'O':
                    ++parse.i; n=-1; l=0;
                    defo=getNum(parse);
                    break;
                case 'l': case 'L':
                    ++parse.i; n=-1; l=0;
                    defl=getNum(parse);
                    break;
                case 'r': case 'R':
                    ++parse.i; n=-1;
                    l=getLen(parse);
                    break;
                default:
                    n=getNote(parse);
                    if(n>=0)
                        l=getLen(parse);
                    else
                        l=0;
                    break;
                }
                if(n>=0){
                    n=(defo-this.octadj)*12+n;
                    if(tie && evlast && evlast.n==n){
                        evlast.g+=l;
                        tie=0;
                    }
                    else
                        this.sequence.push(evlast={t:t,n:n,g:l,f:0});
                }
                t+=l;
            }
            this.redraw();
        };
        this.getMMLString=function(){
            function makeNote(n,l,tb){
                var mmlnote="";
                var ltab=[
                    [960,"1"],[840,"2.."],[720,"2."],[480,"2"],
                    [420,"4.."],[360,"4."],[240,"4"],
                    [210,"8.."],[180,"8."],[120,""],
                    [105,"16.."],[90,"16."],[60,"16"],
                    [45,"32."],[30,"32"],[16,"60"],[15,"64"],
                    [8,"120"],[4,"240"],[2,"480"],[1,"960"]
                ];
                l=l*960/tb;
                while(l>0){
                    for(let j=0;j<ltab.length;++j){
                        while(l>=ltab[j][0]){
                            l-=ltab[j][0];
                            mmlnote+="&"+n+ltab[j][1];
                        }
                    }
                }
                return mmlnote.substring(1);
            }
            var mml="t"+this.tempo+"o4l8";
            var ti=0,meas=0,oct=5,n;
            var notes=["c","d-","d","e-","e","f","g-","g","a-","a","b-","b"];
            for(let i=0;i<this.sequence.length;++i) {
                var ev=this.sequence[i];
                if(ev.t>ti) {
                    var l=ev.t-ti;
                    mml+=makeNote("r",l,this.timebase);
                    ti=ev.t;
                }
                var n=ev.n;
                if(n<oct*12||n>=oct*12+12){
                    oct=(n/12)|0;
                    mml+="o"+(oct+this.octadj);
                }
                n=notes[n%12];
                var l=ev.g;
                if(i+1<this.sequence.length) {
                    var ev2=this.sequence[i+1];
                    if(ev2.t<ev.t+l) {
                        l=ev2.t-ev.t;
                        ti=ev2.t;
                    }
                    else
                        ti=ev.t+ev.g;
                }
                else
                    ti=ev.t+ev.g;
                mml+=makeNote(n,l,this.timebase);
            }
            return mml;
        };
        this.hitTest=function(pos){
            const ht={t:0,n:0,i:-1,m:" "};
            const l=this.sequence.length;
            if(pos.t==this.menu){
                ht.m="m";
                return ht;
            }
            ht.t=(this.xoffset+(pos.x-this.yruler-this.kbwidth)/this.swidth*this.xrange);
            ht.n=this.yoffset-(pos.y-this.height)/this.steph;
            if(pos.y>=this.height || pos.x>=this.width){
                return ht;
            }
            if(pos.y<this.xruler){
                ht.m="x";
                return ht;
            }
            if(pos.x<this.yruler+this.kbwidth){
                ht.m="y";
                return ht;
            }
            for(let i=0;i<l;++i){
                const ev=this.sequence[i];
                if((ht.n|0)==ev.n){
                    if(ev.f && Math.abs(ev.t-ht.t)*this.stepw<8){
                        ht.m="B";
                        ht.i=i;
                        return ht;
                    }
                    if(ev.f && Math.abs(ev.t+ev.g-ht.t)*this.stepw<8){
                        ht.m="E";
                        ht.i=i;
                        return ht;
                    }
                    if(ht.t>=ev.t&&ht.t<ev.t+ev.g){
                        ht.i=i;
                        if(this.sequence[i].f)
                            ht.m="N";
                        else
                            ht.m="n";
                        return ht;
                    }
                }
            }
            ht.m="s";
            return ht;
        };
        this.addNote=function(t,n,g,v,f){
            if(t>=0 && n>=0 && n<128){
                const ev={t:t,c:0x90,n:n,g:g,v:v,f:f};
                this.sequence.push(ev);
                this.sortSequence();
                this.redraw();
                return ev;
            }
            return null;
        };
        this.selAreaNote=function(t1,t2,n1,n2){
            let t, i=0, e=this.sequence[i];
            if(n1>n2)
                t=n1,n1=n2,n2=t;
            if(t1>t2)
                t=t1,t1=t2,t2=t;
            while(e){
                if(e.t>=t1 && e.t<t2 && e.n>=n1 && e.n <= n2)
                    e.f=1;
                else
                    e.f=0;
                e=this.sequence[++i];
            }
        };
        this.delNote=function(idx){
            this.sequence.splice(idx,1);
            this.redraw();
        };
        this.delAreaNote=function(t,g,n){
            const l=this.sequence.length;
            for(let i=l-1;i>=0;--i){
                const ev=this.sequence[i];
                if(typeof(n)!="undefined" && n!=i){
                    if(t<=ev.t && t+g>=ev.t+ev.g){
                        this.sequence.splice(i,1);
                    }
                    else if(t<=ev.t && t+g>ev.t && t+g<ev.t+ev.g){
                        ev.g=ev.t+ev.g-(t+g);
                        ev.t=t+g;
                    }
                    else if(t>=ev.t && t<ev.t+ev.g && t+g>=ev.t+ev.g){
                        ev.g=t-ev.t;
                    }
                    else if(t>ev.t && t+g<ev.t+ev.g){
                        this.addNote(t+g,ev.n,ev.t+ev.g-t-g,this.defvelo);
                        ev.g=t-ev.t;
                    }
                }
            }
        };
        this.delSelectedNote=function(){
            const l=this.sequence.length;
            for(let i=l-1;i>=0;--i){
                const ev=this.sequence[i];
                if(ev.f)
                    this.sequence.splice(i,1);
            }
        };
        this.moveSelectedNote=function(dt,dn){
            const l=this.sequence.length;
            for(let i=0;i<l;++i){
                const ev=this.sequence[i];
                if(ev.f && ev.ot+dt<0)
                    dt=-ev.ot;
            }
            for(let i=0;i<l;++i){
                const ev=this.sequence[i];
                if(ev.f){
                    ev.t=(((ev.ot+dt)/this.snap+.5)|0)*this.snap;
                    ev.n=ev.on+dn;
                }
            }
        };
        this.clearSel=function(){
            const l=this.sequence.length;
            for(let i=0;i<l;++i){
                this.sequence[i].f=0;
            }
        };
        this.selectedNotes=function(){
            let obj=[];
            for(let i = this.sequence.length - 1; i >= 0; --i){
                const ev=this.sequence[i];
                if(ev.f)
                    obj.push({i:i, ev:ev, t:ev.t, g:ev.g});
            }
            return obj;
        };
        this.editDragDown=function(pos){
            const ht=this.hitTest(pos);
            let ev;
            if(ht.m=="N"){
                ev=this.sequence[ht.i];
                this.dragging={o:"D",m:"N",i:ht.i,t:ht.t,n:ev.n,dt:ht.t-ev.t};
                for(let i=0,l=this.sequence.length;i<l;++i){
                    ev=this.sequence[i];
                    if(ev.f)
                        ev.on=ev.n, ev.ot=ev.t, ev.og=ev.g;
                }
                this.redraw();
            }
            else if(ht.m=="n"){
                ev=this.sequence[ht.i];
                this.clearSel();
                ev.f=1;
                this.redraw();
            }
            else if(ht.m=="E"){
                const ev = this.sequence[ht.i];
                this.dragging={o:"D", m:"E", i:ht.i, t:ev.t, g:ev.g, ev:this.selectedNotes()};
            }
            else if(ht.m=="B"){
                const ev = this.sequence[ht.i];
                this.dragging={o:"D", m:"B", i:ht.i, t:ev.t, g:ev.g, ev:this.selectedNotes()};
            }
            else if(ht.m=="s"&&ht.t>=0){
                this.clearSel();
                var t=((ht.t/this.snap)|0)*this.snap;
                this.sequence.push({t:t, n:ht.n|0, g:1, f:1});
                this.dragging={o:"D",m:"E",i:this.sequence.length-1, t:t, g:1, ev:[{t:t,g:1,ev:this.sequence[this.sequence.length-1]}]};
                this.redraw();
            }
        };
        this.editDragMove=function(pos){
            const ht=this.hitTest(pos);
            let ev,t;
            if(this.dragging.o=="D"){
                switch(this.dragging.m){
                case "E":
                    if(this.dragging.ev){
                        const dt=((Math.max(0,ht.t)/this.snap+0.9)|0)*this.snap - this.dragging.t - this.dragging.g;
                        const list=this.dragging.ev;
                        for(let i = list.length - 1; i >= 0; --i){
                            const ev = list[i].ev;
                            ev.g = list[i].g + dt;
                            if(ev.g <= 0)
                                ev.g = 1;
                            if(this.editmove=="dragmono")
                                this.delAreaNote(ev.t,ev.g);
                        }

                    }
                    this.redraw();
                    break;
                case "B":
                    if(this.dragging.ev){
                        const dt=((Math.max(0,ht.t)/this.snap+0.9)|0)*this.snap - this.dragging.t;
                        const list=this.dragging.ev;
                        for(let i = list.length - 1; i >= 0; --i){
                            const ev = list[i].ev;
                            ev.t = list[i].t + dt;
                            ev.g = list[i].g - dt;
                            if(ev.g <= 0)
                                ev.g = 1;
                            if(this.editmove=="dragmono")
                                this.delAreaNote(ev.t,ev.g);
                        }

                    }
                    this.redraw();
                    break;

                ev=this.sequence[this.dragging.i];
                    t=((Math.max(0,ht.t)/this.snap+0.5)|0)*this.snap;
                    ev.g=ev.t+ev.g-t;
                    ev.t=t;
                    if(ev.g<0){
                        ev.t+=ev.g;
                        ev.g=-ev.g;
                        this.dragging.m="E";
                    }
                    else if(ev.g==0){
                        ev.t=t-1;
                        ev.g=1;
                    }
                    this.redraw();
                    break;
                case "N":
                    ev=this.sequence[this.dragging.i];
                    this.moveSelectedNote((ht.t-this.dragging.t)|0, (ht.n|0)-this.dragging.n);
                    this.redraw();
                    break;
                }
            }
        };
        this.editGridDown=function(pos){
            const ht=this.hitTest(pos);
            if(ht.m=="n"){
                this.delNote(ht.i);
                this.dragging={o:"G",m:"0"};
            }
            else if(ht.m=="s"&&ht.t>=0){
                const pt=Math.floor(ht.t);
                if(this.editmode=="gridmono")
                    this.delAreaNote(pt,1,ht.i);
                this.addNote(pt,ht.n|0,1,this.defvelo);
                this.dragging={o:"G",m:"1"};
            }
        };
        this.editGridMove=function(pos){
            const ht=this.hitTest(pos);
            if(this.dragging.o=="G"){
                switch(this.dragging.m){
                case "1":
                    const px=Math.floor(ht.t);
                    if(ht.m=="s"){
                        if(this.editmode=="gridmono")
                            this.delAreaNote(px,1,ht.i);
                        this.addNote(px,ht.n|0,1,this.defvelo);
                    }
                    break;
                case "0":
                    if(ht.m=="n")
                        this.delNote(ht.i);
                    break;
                }
            }
        };
        this.setListener=function(el,mode){
            this.bindcontextmenu = this.contextmenu.bind(this);
            this.bindpointermove = this.pointermove.bind(this);
            this.bindcancel = this.cancel.bind(this);
            el.addEventListener("mousedown",this.pointerdown.bind(this),true);
            el.addEventListener("touchstart",this.pointerdown.bind(this),false);
            if(mode){
                el.addEventListener("mouseover",this.pointerover.bind(this),false);
                el.addEventListener("mouseout",this.pointerout.bind(this),false);
            }
        };
        this.ready=function(){
            this.body=root.children[1];
            this.elem=root.childNodes[2];
            this.proll = this.elem.children[0];
            this.canvas = this.elem.children[0];
            this.kb = this.elem.children[1];
            this.ctx=this.canvas.getContext("2d");
            this.kbimg=this.elem.children[1];
            this.markstartimg=this.elem.children[2];
            this.markendimg=this.elem.children[3];
            this.cursorimg=this.elem.children[4];
            this.menu=this.elem.children[5];
            this.rcMenu={x:0, y:0, width:0, height:0};
            this.lastx=0;
            this.lasty=0;
            this.canvas.addEventListener('mousemove',this.mousemove.bind(this),false);
            this.canvas.addEventListener('keydown',this.keydown.bind(this),false);
            this.canvas.addEventListener('DOMMouseScroll',this.wheel.bind(this),false);
            this.canvas.addEventListener('mousewheel',this.wheel.bind(this),false);
            this.setListener(this.canvas,true);
            this.setListener(this.markendimg,true);
            this.setListener(this.markstartimg,true);
            this.setListener(this.cursorimg,true);
            this.setListener(this.menu,false);
            this.sequence=[];
            this.dragging={o:null};
            this.kbimg.style.height=this.sheight+"px";
            this.kbimg.style.backgroundSize=(this.steph*12)+"px";
            this.layout();
            this.initialized=1;
            this.redraw();
        };
        this.setupImage=function(){
        };
        this.preventScroll=function(e){
            if(e.preventDefault)
                e.preventDefault();
        };
        this.getPos=function(e){
            let t=null;
            if(e){
                t=e.target;
                this.lastx=e.clientX-this.rcTarget.left;
                this.lasty=e.clientY-this.rcTarget.top;
            }
            if(this.lastx>=this.rcMenu.x&&this.lastx<this.rcMenu.x+this.rcMenu.width
                    &&this.lasty>=this.rcMenu.y&&this.lasty<this.rcMenu.y+this.rcMenu.height)
                t=this.menu;
            return {t:t, x:this.lastx, y:this.lasty};
        };
        this.contextmenu= function(e){
            e.stopPropagation();
            e.preventDefault();
            window.removeEventListener("contextmenu",this.bindcontextmenu);
            return false;
        };
        this.keydown=function(e){
            switch(e.keyCode){
            case 46://delNote
                this.delSelectedNote();
                this.redraw();
                break;
            }
        };
        this.popMenu=function(pos){
            const s=this.menu.style;
            s.display="block";
            s.top=(pos.y+8)+"px";
            s.left=(pos.x+8)+"px";
            this.rcMenu=this.menu.getBoundingClientRect();
        };
        this.longtapcountup=function(){
            if(++this.longtapcount >= 18){
                clearInterval(this.longtaptimer);
                switch(this.downht.m){
                case "N":
                case "B":
                case "E":
                    this.popMenu(this.downpos);
                    this.dragging={o:"m"};
                    break;
                }
            }
        };
        this.pointerdown=function(ev) {
            let e;
            if(!this.enable)
                return;
            if(ev.touches)
                e = ev.touches[0];
            else
                e = ev;
            this.rcTarget=this.canvas.getBoundingClientRect();
            this.downpos=this.getPos(e);
            this.downht=this.hitTest(this.downpos);

            this.longtapcount = 0;
            this.longtaptimer = setInterval(this.longtapcountup.bind(this),100);
            window.addEventListener("touchmove", this.bindpointermove,false);
            window.addEventListener("mousemove",this.bindpointermove,false);
            window.addEventListener("touchend",this.bindcancel);
            window.addEventListener("mouseup",this.bindcancel);
            window.addEventListener("contextmenu",this.bindcontextmenu);

            if(e.button==2||e.ctrlKey){
                switch(this.downht.m){
                case "N":
                case "B":
                case "E":
                    this.popMenu(this.downpos);
                    this.dragging={o:"m"};
                    break;
                default:
                    if(this.editmode=="dragmono"||this.editmode=="dragpoly")
                        this.dragging={o:"A",p:this.downpos,p2:this.downpos,t1:this.downht.t,n1:this.downht.n};
                    break;
                }
                ev.preventDefault();
                ev.stopPropagation();
                this.canvas.focus();
                return false;
            }
            switch(e.target){
            case this.markendimg:
                this.dragging={o:"E",x:this.downpos.x,m:this.markend};
                ev.preventDefault();
                ev.stopPropagation();
                return false;
            case this.markstartimg:
                this.dragging={o:"S",x:this.downpos.x,m:this.markstart};
                ev.preventDefault();
                ev.stopPropagation();
                return false;
            case this.cursorimg:
                this.dragging={o:"P",x:this.downpos.x,m:this.cursor};
                ev.preventDefault();
                ev.stopPropagation();
                return false;
            }

            if(this.downht.m=="x"){
                this.dragging={o:"HX",x:this.downpos.x,y:this.downpos.y,t:this.downht.t,offsx:this.xoffset,xrange:this.xrange};
                ev.preventDefault();
                ev.stopPropagation();
                return false;
            }
            if(this.downht.m=="y"){
                this.dragging={o:"HY",x:this.downpos.x,y:this.downpos.y,n:this.downht.n,offsy:this.yoffset,yrange:this.yrange};
                ev.preventDefault();
                ev.stopPropagation();
                return false;
            }
            this.dragging={o:null,x:this.downpos.x,y:this.downpos.y,offsx:this.xoffset,offsy:this.yoffset};
            this.canvas.focus();
            switch(this.editmode){
            case "gridpoly":
            case "gridmono":
                this.editGridDown(this.downpos);
                break;
            case "dragpoly":
            case "dragmono":
                this.editDragDown(this.downpos);
                break;
            }
            this.press = 1;
            if(ev.preventDefault)
                ev.preventDefault();
            if(ev.stopPropagation)
                ev.stopPropagation();
            return false;
        };
        this.mousemove=function(e){
            if(this.dragging.o==null){
                this.rcTarget=this.canvas.getBoundingClientRect();
                const pos=this.getPos(e);
                const ht=this.hitTest(pos);
                switch(ht.m){
                    case "E": this.canvas.style.cursor="e-resize"; break;
                    case "B": this.canvas.style.cursor="w-resize"; break;
                    case "N": this.canvas.style.cursor="move"; break;
                    case "n": this.canvas.style.cursor="pointer"; break;
                    case "s": this.canvas.style.cursor="pointer"; break;
                    }
                }
        };
        this.pointermove=function(ev) {
            let e;
            this.rcTarget=this.canvas.getBoundingClientRect();
            if(ev.touches)
                e = ev.touches[0];
            else
                e = ev;
            if(this.longtaptimer)
                clearInterval(this.longtaptimer);
            const pos=this.getPos(e);
            const ht=this.hitTest(pos);
            switch(this.dragging.o){
            case null:
                if(this.xscroll)
                    this.xoffset=this.dragging.offsx+(this.dragging.x-pos.x)*(this.xrange/this.width);
                if(this.yscroll)
                    this.yoffset=this.dragging.offsy+(pos.y-this.dragging.y)*(this.yrange/this.height);
                break;
            case "HX":
                var dx = pos.x - this.dragging.x;
                var dy = pos.y - this.dragging.y;
                if(Math.abs(dy) > Math.abs(dx)){
                    var f = Math.pow(1.01, dy);
                    this.xoffset = this.dragging.t - (this.dragging.t - this.dragging.offsx) * f;
                    this.xrange = this.dragging.xrange * f;
                }else{
                    this.xoffset=this.dragging.offsx+(this.dragging.x-pos.x)*(this.xrange/this.width);
                }
                break;
            case "HY":
                var dx = pos.x - this.dragging.x;
                var dy = pos.y - this.dragging.y;
                if(Math.abs(dx) > Math.abs(dy)){
                    var f = Math.pow(1.01, dx);
                    this.yoffset = this.dragging.n - (this.dragging.n - this.dragging.offsy) * f;
                    this.yrange = this.dragging.yrange * f;
                }else{
                    this.yoffset=this.dragging.offsy+(pos.y-this.dragging.y)*(this.yrange/this.height);
                }
                break;
            case "m":
                if(ht.m=="m"){
                    this.menu.style.background="#ff6";
                }
                else {
                    this.menu.style.background="#eef";
                }
                break;
            case "A":
                this.dragging.p2=pos;
                this.dragging.t2=ht.t;
                this.dragging.n2=ht.n;
                this.redraw();
                break;
            case "E":
                var p=Math.max(1,(this.dragging.m+(pos.x-this.dragging.x)/this.stepw+.5)|0);
                if(this.markstart>=p)
                    this.markstart=p-1;
                this.markend=p;
                break;
            case "S":
                var p=Math.max(0,(this.dragging.m+(pos.x-this.dragging.x)/this.stepw+.5)|0);
                if(this.markend<=p)
                    this.markend=p+1;
                this.markstart=p;
                break;
            case "P":
                this.cursor=Math.max(0,(this.dragging.m+(pos.x-this.dragging.x)/this.stepw+.5)|0);
                break;
            }
            switch(this.editmode){
            case "gridpoly":
            case "gridmono":
                this.editGridMove(pos);
                break;
            case "dragpoly":
            case "dragmono":
                this.editDragMove(pos);
                break;
            }
//            ev.preventDefault();
            ev.stopPropagation();
            return false;
        };
        this.cancel= function(ev) {
            let e;
            if(ev.touches)
                e = null;
            else
                e = ev;
            if(this.longtaptimer)
                clearInterval(this.longtaptimer);
            const pos=this.getPos(e);
            if(this.dragging.o=="m"){
                this.menu.style.display="none";
                this.rcMenu={x:0,y:0,width:0,height:0};
                if(pos.t==this.menu)
                    this.delSelectedNote();
                this.redraw();
            }
            if(this.dragging.o=="A"){
                this.selAreaNote(this.dragging.t1,this.dragging.t2,this.dragging.n1,this.dragging.n2);
                this.dragging={o:null};
                this.redraw();
            }
//            if(this.dragging.o=="D"){
                if(this.editmode=="dragmono"){
                    for(let ii=this.sequence.length-1;ii>=0;--ii){
                        const ev=this.sequence[ii];
                        if(ev && ev.f){
                            this.delAreaNote(ev.t,ev.g,ii);
                        }
                    }
                }
                this.redraw();
//            }
            this.dragging={o:null};
            if(this.press){
                this.sortSequence();
            }
            this.press = 0;
//            this.mousemove(e);
            window.removeEventListener('touchstart',this.preventScroll,false);
            window.removeEventListener("mousemove",this.bindpointermove,false);
            window.removeEventListener("touchend",this.bindcancel,false);
            window.removeEventListener("mouseup",this.bindcancel,false);
            ev.preventDefault();
            ev.stopPropagation();
//            window.removeEventListener("contextmenu",this.contextmenu);
            return false;
        };
        this.pointerover=function(e) {
        };
        this.pointerout=function(e) {
//            window.removeEventListener("contextmenu",this.contextmenu);
        };
        this.wheel=function(e) {
            let delta = 0;
            const pos=this.getPos(e);
            if(!e)
                e = window.event;
            if(e.wheelDelta)
                delta = e.wheelDelta/120;
            else if(e.detail)
                delta = -e.detail/3;
            const ht=this.hitTest(pos);
            if((this.wheelzoomx||this.wheelzoom) && ht.m=="x"){
                if(delta>0){
                    this.xoffset=ht.t-(ht.t-this.xoffset)/1.2
                    this.xrange/=1.2;
                }
                else{
                    this.xoffset=ht.t-(ht.t-this.xoffset)*1.2
                    this.xrange*=1.2;
                }
            }
            if((this.wheelzoomy||this.wheelzoom) && ht.m=="y"){
                if(delta>0){
                    this.yoffset=ht.n-(ht.n-this.yoffset)/1.2
                    this.yrange/=1.2;
                }
                else{
                    this.yoffset=ht.n-(ht.n-this.yoffset)*1.2
                    this.yrange*=1.2;
                }

            }
            e.preventDefault();
        };
        this.layout=function(){
            if(typeof(this.kbwidth)=="undefined")
                return;
            const proll = this.proll;
            const bodystyle = this.body.style;
            if(this.bgsrc)
                proll.style.background="url('"+this.bgsrc+"')";
            this.kbimg.style.background="url('"+this.kbsrc+"')";
            if(this.width){
                proll.width = this.width;
                bodystyle.width = proll.style.width = this.width+"px";
            }
            if(this.height) {
                proll.height = this.height;
                bodystyle.height = proll.style.height = this.height+"px";
            }
            this.swidth=proll.width-this.yruler;
            this.swidth-=this.kbwidth;
            this.sheight=proll.height-this.xruler;
            this.redraw();
        };
        this.redrawMarker=function(){
            if(!this.initialized)
                return;
            const cur=(this.cursor-this.xoffset)*this.stepw+this.yruler+this.kbwidth;
            this.cursorimg.style.left=(cur+this.cursoroffset)+"px";
            const start=(this.markstart-this.xoffset)*this.stepw+this.yruler+this.kbwidth;
            this.markstartimg.style.left=(start+this.markstartoffset)+"px";
            const end=(this.markend-this.xoffset)*this.stepw+this.yruler+this.kbwidth;
            this.markendimg.style.left=(end+this.markendoffset)+"px";
        };
        this.redrawGrid=function(){
            for(let y=0;y<128;++y){
                if(this.semiflag[y%12]&1)
                    this.ctx.fillStyle=this.coldk;
                else
                    this.ctx.fillStyle=this.collt;
                let ys = this.height - (y - this.yoffset) * this.steph;
                this.ctx.fillRect(this.yruler+this.kbwidth, ys|0, this.swidth,-this.steph);
                this.ctx.fillStyle=this.colgrid;
                this.ctx.fillRect(this.yruler+this.kbwidth, ys|0, this.swidth,1);
            }
            for(let t=0;;t+=this.grid){
                let x=this.stepw*(t-this.xoffset)+this.yruler+this.kbwidth;
                this.ctx.fillRect(x|0,this.xruler,1,this.sheight);
                if(x>=this.width)
                    break;
            }
        };
        this.semiflag=[6,1,0,1,0,2,1,0,1,0,1,0];
        this.redrawXRuler=function(){
            if(this.xruler){
                this.ctx.textAlign="left";
                this.ctx.font=(this.xruler/2)+"px 'sans-serif'";
                this.ctx.fillStyle=this.colrulerbg;
                this.ctx.fillRect(0,0,this.width,this.xruler);
                this.ctx.fillStyle=this.colrulerborder;
                this.ctx.fillRect(0,0,this.width,1);
                this.ctx.fillRect(0,0,1,this.xruler);
                this.ctx.fillRect(0,this.xruler-1,this.width,1);
                this.ctx.fillRect(this.width-1,0,1,this.xruler);
                this.ctx.fillStyle=this.colrulerfg;
                for(let t=0;;t+=this.timebase){
                    let x=(t-this.xoffset)*this.stepw+this.yruler+this.kbwidth;
                    this.ctx.fillRect(x,0,1,this.xruler);
                    this.ctx.fillText(t/this.timebase+1,x+4,this.xruler-8);
                    if(x>=this.width)
                        break;
                }
            }
        };
        this.redrawYRuler=function(){
            if(this.yruler){
                this.ctx.textAlign="right";
                this.ctx.font=(this.steph/2)+"px 'sans-serif'";
                this.ctx.fillStyle=this.colrulerbg;
                this.ctx.fillRect(0,this.xruler,this.yruler,this.sheight);
                this.ctx.fillStyle=this.colrulerborder;
                this.ctx.fillRect(0,this.xruler,1,this.sheight);
                this.ctx.fillRect(this.yruler,this.xruler,1,this.sheight);
                this.ctx.fillRect(0,this.height-1,this.yruler,1);
                this.ctx.fillStyle=this.colrulerfg;
                for(let y=0;y<128;y+=12){
                    const ys=this.height-this.steph*(y-this.yoffset);
                    this.ctx.fillRect(0,ys|0,this.yruler,-1);
                    this.ctx.fillText("C"+(((y/12)|0)+this.octadj),this.yruler-4,ys-4);
                }
            }
            this.kbimg.style.top=(this.xruler)+"px";
            this.kbimg.style.left=this.yruler+"px";
            this.kbimg.style.width=this.kbwidth+"px";
            this.kbimg.style.backgroundSize="100% "+(this.steph*12)+"px";
            this.kbimg.style.backgroundPosition="0px "+(this.sheight+this.steph*this.yoffset)+"px";
        };
        this.redrawKeyboard=function(){
            if(this.yruler){
                this.ctx.textAlign="right";
                this.ctx.font=(this.steph/2)+"px 'sans-serif'";
                this.ctx.fillStyle=this.colortab.kbwh;
                this.ctx.fillRect(1,this.xruler,this.yruler,this.sheight);
                this.ctx.fillStyle=this.colortab.kbbk;
                for(y=0;y<128;++y){
                    const ys=this.height-this.steph*(y-this.yoffset);
                    const ysemi=y%12;
                    const fsemi=this.semiflag[ysemi];
                    if(fsemi&1){
                        this.ctx.fillRect(0,ys,this.yruler/2,-this.steph);
                        this.ctx.fillRect(0,(ys-this.steph/2)|0,this.yruler,-1);
                    }
                    if(fsemi&2)
                        this.ctx.fillRect(0,ys|0,this.yruler,-1);
                    if(fsemi&4)
                        this.ctx.fillText("C"+(((y/12)|0)+this.octadj),this.yruler-4,ys-4);
                }
                this.ctx.fillRect(this.yruler,this.xruler,1,this.sheight);
            }
        };
        this.redrawAreaSel=function(){
            if(this.dragging && this.dragging.o=="A"){
                this.ctx.fillStyle=this.colselarea;
                this.ctx.fillRect(this.dragging.p.x,this.dragging.p.y,this.dragging.p2.x-this.dragging.p.x,this.dragging.p2.y-this.dragging.p.y);
            }
        };
        this.redraw=function() {
            let x,w,y,x2,y2;
            if(!this.ctx)
                return;
            this.ctx.clearRect(0,0,this.width,this.height);
            this.stepw = this.swidth/this.xrange;
            this.steph = this.sheight/this.yrange;
            this.redrawGrid();
            const l=this.sequence.length;
            for(let s=0; s<l; ++s){
                const ev=this.sequence[s];
                if(ev.f)
                    this.ctx.fillStyle=this.colnotesel;
                else
                    this.ctx.fillStyle=this.colnote;
                w=ev.g*this.stepw;
                x=(ev.t-this.xoffset)*this.stepw+this.yruler+this.kbwidth;
                x2=(x+w)|0; x|=0;
                y=this.height - (ev.n-this.yoffset)*this.steph;
                y2=(y-this.steph)|0; y|=0;
                this.ctx.fillRect(x,y,x2-x,y2-y);
                if(ev.f)
                    this.ctx.fillStyle=this.colnoteselborder;
                else
                    this.ctx.fillStyle=this.colnoteborder;
                this.ctx.fillRect(x,y,1,y2-y);
                this.ctx.fillRect(x2,y,1,y2-y);
                this.ctx.fillRect(x,y,x2-x,1);
                this.ctx.fillRect(x,y2,x2-x,1);
            }
            this.redrawYRuler();
            this.redrawXRuler();
            this.redrawMarker();
            this.redrawAreaSel();
        };
        this.ready();
    }
    sendEvent(ev){
        let event;
        event=document.createEvent("HTMLEvents");
        event.initEvent(ev,false,true);
        this.dispatchEvent(event);
    }
    getAttr(n,def){
        let v=this.getAttribute(n);
        if(v==""||v==null) return def;
        switch(typeof(def)){
        case "number":
          if(v=="true") return 1;
          v=+v;
          if(isNaN(v)) return 0;
          return v;
        }
        return v;
    }
    disconnectedCallback(){}
});
